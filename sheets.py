import importlib
import os
import time

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from discord import File
from discord.ext import commands

import imgreader

# If modifying these scopes, delete the file token.json.
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class ScoreHandler(commands.Cog):
    def __init__(self, bot):
        # For channel fetching purposes
        self._bot = bot

        # Reload dependency as well
        importlib.reload(imgreader)

        # Authenticate to Google Sheets API
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('sheets', 'v4', credentials=creds)
        self._sheets = service.spreadsheets()
        self._sheet_id = os.getenv('SPREADSHEET_ID')

        self._image_channel = None
        self._summary_channel = None

    @commands.Cog.listener()
    async def on_ready(self):
        # Populate channels
        self._image_channel = self._bot.get_channel(os.getenv('IMG_CHANNEL_ID'))
        self._image_channel = self._image_channel or await self._bot.fetch_channel(os.getenv('IMG_CHANNEL_ID'))
        self._summary_channel = self._bot.get_channel(os.getenv('SUM_CHANNEL_ID'))
        self._summary_channel = self._summary_channel or await self._bot.fetch_channel(os.getenv('SUM_CHANNEL_ID'))

        # Check messages that we might have missed
        pass

    @commands.Cog.listener()
    async def on_message(self, msg):
        # Check submissions and mark them as they're processed
        if msg.channel == self._image_channel:
            await self.process_message(msg)

    async def process_message(self, msg):
        # print('Converting message to image...')
        result = await imgreader.message_to_image(msg)
        if result is None:
            await msg.add_reaction('❌')
            return
        elif result == -1:  # no image found
            return

        # Get spreadsheet fields
        img_buffer, score = result
        user_id = str(msg.author.id)
        timestamp = time.time()
        msg_link = msg.jump_url

        # Post summary image with message link attached
        # print('Posting to summary channel...')
        summary_msg = await self._summary_channel.send(msg_link, file=File(img_buffer, 'image.png'))
        summary_link = summary_msg.jump_url

        # Update spreadsheet
        # print('Updating spreadsheet...')
        values = [[user_id, score, timestamp, summary_link]]
        result = self._sheets.values().append(spreadsheetId=self._sheet_id,
                                              range='A:D',
                                              valueInputOption='RAW',
                                              insertDataOption='INSERT_ROWS',
                                              body={'values': values}).execute()
        num_updated = result.get('updates').get('updatedCells')

        if num_updated:
            await msg.add_reaction('✅')
        else:
            await msg.add_reaction('❌')


def setup(bot):
    bot.add_cog(ScoreHandler(bot))
