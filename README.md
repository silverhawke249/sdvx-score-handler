# sdvx-score-handler
Requires:
- python-dotenv
- discord.py
- opencv

## Required files
The following files are required but not included for privacy reasons:
- .env

### .env
The following variables are required:
- DISCORD_TOKEN
  - Needed to log in as bot user
- BOT_HANDLER_ID
  - Discord role ID of the role that is allowed to manage the bot
- IMG_CHANNEL_ID
  - Channel ID of the channel where the bot will listen for messages
- SUM_CHANNEL_ID
  - Channel ID of the channel where the bot will post summaries

## To-dos
- [ ] ~~Track last seen message~~
- [x] Implement catch-up processing of messages not seen before
- [ ] Digit recognition for BT/LONG/VOL breakdown
- [ ] ~~Explain how to create `credentials.json`~~
- [x] Migrate out of Google Sheets (this obsoletes the previous to-do)
