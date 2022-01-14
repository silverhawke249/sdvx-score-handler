from audioop import reverse
import importlib
import os
import pickle
import time

import discord
from dotenv import load_dotenv
from discord.ext import commands

import imgreader

load_dotenv()
DB_PATH = 'score_db.dat'
ALLOWED_KEYS = ['timestamp', 'user_id', 'score', 'chain_bt', 'chain_long', 'chain_vol', 'message_link']


class ScoreHandler(commands.Cog):
    def __init__(self, bot: discord.Client):
        # For channel fetching purposes
        self._bot = bot

        # Reload dependency as well
        importlib.reload(imgreader)

        try:
            with open(DB_PATH, 'r') as f:
                self._db = pickle.load(f)
        except IOError:
            self._db = []

        self._image_channel = None
        self._summary_channel = None

    def _save_data(self, data: dict) -> None:
        data = {k: v for k, v in data.items() if k in ALLOWED_KEYS}
        self._db.append(data)
        with open(DB_PATH, 'w') as f:
            pickle.dump(self._db, f)

    @commands.Cog.listener()
    async def on_ready(self):
        # Populate channels
        self._image_channel = self._bot.get_channel(os.getenv('IMG_CHANNEL_ID'))
        self._image_channel = self._image_channel or await self._bot.fetch_channel(os.getenv('IMG_CHANNEL_ID'))
        self._summary_channel = self._bot.get_channel(os.getenv('SUM_CHANNEL_ID'))
        self._summary_channel = self._summary_channel or await self._bot.fetch_channel(os.getenv('SUM_CHANNEL_ID'))

        # Check messages that we might have missed
        msg_stack = []
        async for msg in self._image_channel.history(limit=100):
            if any(react.me for react in msg.reactions):
                break
            msg_stack.append(msg)
        
        async for msg in reversed(msg_stack):
            self.process_message(msg)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        # Check submissions and mark them as they're processed
        if msg.channel == self._image_channel:
            await self.process_message(msg)

    async def process_message(self, msg: discord.Message) -> None:
        result = await imgreader.message_to_image(msg)
        if result['status'] == 'error':
            self._bot.log('ImgHandler', f'Error: msg-id={msg.id}, reason={result["msg"]}')
            return

        # Get values that we need to save
        img_buffer, score, chain_totals = result['img'], result['score'], result['totals']
        bt_total, long_total, vol_total = chain_totals
        user_id = str(msg.author.id)
        timestamp = time.time()
        msg_link = msg.jump_url

        # Post summary image with message link attached
        summary_msg = await self._summary_channel.send(msg_link, file=discord.File(img_buffer, 'image.png'))
        summary_link = summary_msg.jump_url

        # Update score database
        self._save_data({
            'timestamp': timestamp,
            'user_id': user_id,
            'score': score,
            'chain_bt': bt_total,
            'chain_long': long_total,
            'chain_vol': vol_total,
            'message_link': summary_link
        })

        await msg.add_reaction('✅')


def setup(bot):
    bot.add_cog(ScoreHandler(bot))
