import cv2
import discord
import io
import numpy as np
import typing

# Result screen template
template = cv2.imread('imgs/template.png')
template_bw = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

# Score numbers
numbers = cv2.imread('imgs/numbers.png')
numbers = cv2.cvtColor(numbers, cv2.COLOR_BGR2GRAY)
_, numbers = cv2.threshold(numbers, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

# Initialize SIFT (might change to ORB or something else)
sift = cv2.SIFT_create()
tkey, tdesc = sift.detectAndCompute(template_bw, None)
matcher = cv2.FlannBasedMatcher({'algorithm': 1, 'trees': 5}, {'checks': 50})

# Other parameters
match_threshold = 75
lowe_threshold = 0.7


async def get_image(msg: discord.Message) -> None | np.ndarray:
    in_img = None
    if msg.attachments:
        for attach_img in msg.attachments:
            try:
                in_img = cv2.imdecode(np.frombuffer(await attach_img.read(), np.uint8), cv2.IMREAD_COLOR)
            except Exception:
                continue

    if in_img is None:
        return

    # Resize image to reasonable dimensions
    # Doing this apparently removes induced Moire patterns? idk
    while in_img.shape[1] > 2400:
        in_img = cv2.resize(in_img, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_LANCZOS4)
    in_img = cv2.resize(in_img, (0, 0), fx=1200/in_img.shape[1],
                        fy=1200/in_img.shape[1], interpolation=cv2.INTER_LANCZOS4)

    return in_img


async def unwarp_image(in_img: np.ndarray) -> None | np.ndarray:
    key, desc = sift.detectAndCompute(cv2.cvtColor(in_img, cv2.COLOR_BGR2GRAY), None)

    # Match features with the desired matcher
    matches = matcher.knnMatch(desc, tdesc, k=2)
    good_points = []
    for m, n in matches:
        if m.distance < lowe_threshold * n.distance:
            good_points.append(m)

    if len(good_points) < match_threshold:
        return

    # Get points to find homography, and then warp the image
    src_pts = np.float32([key[m.queryIdx].pt for m in good_points]).reshape(-1, 1, 2)
    dst_pts = np.float32([tkey[m.trainIdx].pt for m in good_points]).reshape(-1, 1, 2)
    matrix, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    temp_h, temp_w, _ = template.shape
    out_img = cv2.warpPerspective(in_img, matrix, (temp_w, temp_h))

    return out_img


async def crop_image(out_img: np.ndarray) -> np.ndarray:
    # Image output specification:
    # dimensions: 475 x 295
    # jacket resized to 115 x 115
    # diff resized to 115 x 27
    # score resized to 475 x 69
    # black background
    score = out_img[207:262, 438:815]
    song_title = out_img[137:166, 403:878]
    song_artist = out_img[170:200, 403:878]
    diff = out_img[10:30, 205:289]
    details = out_img[338:480, 31:391]
    jacket = out_img[34:306, 23:295]
    card_name = out_img[600:625, 156:425]

    # Slot in all the cropped bits into the summarized image
    img = np.zeros((295, 475, 3), np.uint8)
    img[:25, :269] = card_name
    img[25:94, :] = cv2.resize(score, (475, 69))
    img[94:123, :] = song_title
    img[123:153, :] = song_artist
    img[153:, :360] = details
    img[153:268, 360:] = cv2.resize(jacket, (115, 115))
    img[268:, 360:] = cv2.resize(diff, (115, 27))

    return img


async def read_score(img: np.ndarray) -> int:
    # Image prepping
    score = img[25:94, :]
    score_bw = cv2.resize(score, (475, 69))
    score_bw = cv2.cvtColor(score_bw, cv2.COLOR_BGR2GRAY)
    score_bw = cv2.GaussianBlur(score_bw, (5, 5), 0)
    _, score_bw = cv2.threshold(score_bw, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    # Digit reading
    cur_x = 0
    score_val = 0
    for d in range(8):
        if d < 4:
            dw, dh = 72, 69
        else:
            dw, dh = 48, 46
        # Resize to fit template
        digit = score_bw[-dh:, cur_x:cur_x + dw]
        digit = cv2.resize(digit, (0, 0), fx=52/dw, fy=52/dw)
        cur_x += dw

        # Nothing too fancy, just using template matching
        match_result = cv2.matchTemplate(digit, numbers, cv2.TM_CCOEFF_NORMED)
        topleft_pos = cv2.minMaxLoc(match_result)[3]
        score_val = 10 * score_val + int(topleft_pos[0] / 52 + 0.5)  # rounding, not flooring
        if score_val > 10_000_000:
            score_val %= 10_000_000

    return score_val


async def read_chains(img: np.ndarray) -> typing.Tuple[int, int, int]:
    # TODO: implement this
    return None, None, None


async def message_to_image(msg: discord.Message) -> dict:
    in_img = await get_image(msg)
    if in_img is None:
        return {'status': 'error', 'msg': 'No image found.'}

    out_img = await unwarp_image(in_img)
    if out_img is None:
        return {'status': 'error', 'msg': 'Cannot find score region in image.'}

    final_img = await crop_image(out_img)
    score = await read_score(final_img)
    totals = await read_chains(final_img)

    # Encode image to a bytes sequence, and then put it in
    # BytesIO so that it plays nice with discord.File
    _, out_buffer = cv2.imencode('.png', final_img)
    out_buffer = io.BytesIO(out_buffer)
    return {'status': 'ok',
            'img': out_buffer,
            'score': score,
            'totals': totals}
