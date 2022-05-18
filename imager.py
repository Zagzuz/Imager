import os
import re
import sys
import logging
from enum import Enum
from random import randrange
from google_images_search import GoogleImagesSearch

from telegram import Update, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, \
                         Filters, CallbackContext, Dispatcher


def init_logging(console_level=logging.DEBUG, file_level=logging.DEBUG):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    console_logger = logging.StreamHandler(sys.stdout)
    console_logger.setLevel(console_level)
    console_formatter = logging.Formatter("[%(levelname)-8s] %(message)s")
    console_logger.setFormatter(console_formatter)
    root.addHandler(console_logger)
    filename = f"{os.path.basename(__file__).split('.')[0]}.log"
    file_logger = logging.FileHandler(filename, 'w', 'utf-8')
    file_logger.setLevel(file_level)
    file_formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
    file_logger.setFormatter(file_formatter)
    root.addHandler(file_logger)


def is_local():
    return not (len(sys.argv) > 1 and sys.argv[1] == "remote")

def init_env():
    from dotenv import load_dotenv
    load_dotenv()
    logging.debug("Local environment initialised")


def start_bot(updater: Updater):
    if is_local():
        updater.start_polling()
        logging.debug("Starting locally...")
    else:
        url = f"https://{HEROKU_APP_NAME}.herokuapp.com/{TOKEN}"
        updater.start_webhook(listen="0.0.0.0",
                          port=int(envar("PORT")),
                          url_path=envar("TOKEN"),
                          webhook_url=url)
        logging.debug("Starting on heroku...")
    updater.idle()


def envar(varname: str):
    return os.environ.get(varname, None)


class ResultType(Enum):
    PIC = 0
    GIF = 1


class SearchType(Enum):
    PRECISE = 0
    RANDOM = 1


def cmd_del(upd: Update, ctx: CallbackContext):
    if upd.message is not None and                      \
        upd.message.reply_to_message is not None and    \
        upd.message.from_user is not None and           \
        upd.message.from_user.id == envar("MY_ID"):
        ctx.bot.delete_message(upd.message.reply_to_message.chat.id,
                               upd.message.reply_to_message.message_id)

last_index = 0
last_query = None
search_results = None
last_search_type = None


def parse_query(ctx):
    if not ctx.match or not ctx.match.regs:
        return None
    if ctx.match.regs[2] == (-1, -1):   # no query
        return last_query
    a, b = ctx.match.regs[2]
    return ctx.match.string[a:b].strip()


def search(upd: Update, ctx: CallbackContext, result_type: ResultType, search_type: SearchType):
    if upd.message is None:
        return
    gis = GoogleImagesSearch(envar("API_KEY"), envar("DEVELOPER_GCX"))
    query = parse_query(ctx)
    if query is None:
        return
    global last_query
    global last_index
    global search_results
    global last_search_type
    while True:
        if search_type != last_search_type:
            last_index = 0
        if query != last_query:
            last_index = 0
            ctx.bot.send_chat_action(upd.message.chat.id, ChatAction.TYPING)
            gis.search({'q': query, 'num': 10})
            search_results = gis.results()
        if len(search_results) == 0:
            upd.message.reply_text("Nothing found")
            return
        if search_type == SearchType.RANDOM:
            last_index = randrange(len(search_results))
        else:
            last_index %= len(search_results)
        try:
            ctx.bot.send_chat_action(upd.message.chat.id, ChatAction.UPLOAD_PHOTO)
            upd.message.reply_photo(search_results[last_index].url)
        except:
            del search_results[last_index]
        else:
            break
    if search_type == SearchType.PRECISE:
        last_index += 1
    last_query = query
    last_search_type = search_type


def add_handlers(d: Dispatcher):
    filter_ignorecase = lambda s: Filters.regex(re.compile(s, re.IGNORECASE))
    d.add_handler(MessageHandler(filter_ignorecase("^(дел|del)$"),            cmd_del))
    d.add_handler(MessageHandler(filter_ignorecase("^(pls|плс)( .+)?$"),      lambda u, c: search(u, c, ResultType.PIC, SearchType.RANDOM)))
    d.add_handler(MessageHandler(filter_ignorecase("^(gif|гиф)( .+)?$"),      lambda u, c: search(u, c, ResultType.GIF, SearchType.RANDOM)))
    d.add_handler(MessageHandler(filter_ignorecase("^(gif1|гиф1)( .+)?$"),    lambda u, c: search(u, c, ResultType.GIF, SearchType.PRECISE)))
    d.add_handler(MessageHandler(filter_ignorecase("^(please|плис)( .+)?$"),  lambda u, c: search(u, c, ResultType.PIC, SearchType.PRECISE)))
    d.add_error_handler(lambda u, c: error(c.error))


def main():
    init_logging()
    if is_local():
        init_env()
    updater = Updater(envar("TOKEN"), use_context=True)
    add_handlers(updater.dispatcher)
    start_bot(updater)


if __name__ == '__main__':
    main()