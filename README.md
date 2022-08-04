# Imager
Simple Telegram image-searching bot.
Google Custom Search API is used to get a random or the most relevant picture (or gif animation) on specified query.
Keep in mind there are certain API [restrictions](https://developers.google.com/custom-search/v1/overview#pricing). 

## Requirements
+ [Google-Images-Search](https://github.com/arrrlo/Google-Images-Search)
+ [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v.13.1+
+ [python-dotenv](https://github.com/theskumar/python-dotenv)

## Setup
Create .env file in a root directory and add required envrionmental variables in the following format:
```
API_KEY='<DEVELOP API KEY>'
DEVELOPER_GCX='<DEVELOPER GCX>'
```
More information on how to obtain those on [Google-Images-Search repository page](https://github.com/arrrlo/Google-Images-Search). 
### When using locally
```
TOKEN='<YOUR TELEGRAM BOT TOKEN>'
MY_ID=<YOUR TELEGRAM ID>
```
`MY_ID` is used by the bot to delete its messages on command. Leave it empty if you don't fell you need it.
### When using remotely (webhooks)
Additionally to those listed above, you need to add
```
PORT=<PORT>
```
and if you're deploying on Heroku:
```
HEROKU_APP_NAME=<YOUR HEROKU APP NAME>
```
`PORT` is typically 8443
