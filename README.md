# sdvx-score-handler
Requires:
- python-dotenv
- discord.py
- opencv
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib

## Required files
The following files are required but not included for privacy reasons:
- .env
- credentials.json
- token.json

### .env file
The following variables are required:
- DISCORD_TOKEN
  - Needed to log in as bot user
- SPREADSHEET_ID
  - Sheets ID of spreadsheet used to write to and read from
  - This spreadsheet must have at least 4 columns
- BOT_HANDLER_ID
  - Discord role ID of the role that is allowed to manage the bot
- IMG_CHANNEL_ID
  - Channel ID of the channel where the bot will listen for messages
- SUM_CHANNEL_ID
  - Channel ID of the channel where the bot will post summaries

### credentials.json
This file is required for the bot to access Google APIs.

For more info, see <https://developers.google.com/sheets/api/quickstart/python>.

### token.json
This file is generated once you authenticate the bot through OAuth2.

## To-dos
- [ ] Track last seen message
- [ ] Implement catch-up processing of messages not seen before
- [ ] Digit recognition for BT/LONG/VOL breakdown
- [ ] Explain how to create `credentials.json`.
