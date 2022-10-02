import re
import os
import sys
import logging
from utils import envar
from random import randrange

import search

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
        url = f"https://{envar('HEROKU_APP_NAME')}.herokuapp.com/{envar('TOKEN')}"
        updater.start_webhook(listen="0.0.0.0",
                          port=int(envar("PORT")),
                          url_path=envar("TOKEN"),
                          webhook_url=url)
        logging.debug("Starting on heroku...")
    updater.idle()


def cmd_del(upd: Update, ctx: CallbackContext):
    if upd.message is not None and                      \
        upd.message.reply_to_message is not None and    \
        upd.message.from_user is not None and           \
        upd.message.from_user.id == int(envar("MY_ID")):
        ctx.bot.delete_message(upd.message.reply_to_message.chat.id,
                               upd.message.reply_to_message.message_id)


def parse_query(ctx):
    if not ctx.match or not ctx.match.regs:
        return None
    if ctx.match.regs[2] == (-1, -1):   # no query
        return ctx.chat_data["engine"].query
    a, b = ctx.match.regs[2]
    return ctx.match.string[a:b].strip()


def init_chat_data(ctx):
    def inner(ctx, **kwargs):
        for k, v in kwargs.items():
            if k not in ctx.chat_data:
                ctx.chat_data[k] = v
    kwargs = {"engine": search.Engine(),
              "index" : search.Index(),
              "type"  : None}
    inner(ctx, **kwargs)


def searcher(upd: Update, ctx: CallbackContext, result_type: search.ResultType, search_type: search.Type, attempts=10):
    init_chat_data(ctx)
    # Get query
    if upd.message is None:
        return
    query = parse_query(ctx)
    if query is None:
        return
    res = ctx.chat_data["engine"].results
    # If this is a new query or a different result type - start searching
    if query != ctx.chat_data["engine"].query or \
       result_type != ctx.chat_data["engine"].result_type:
       ctx.chat_data["index"].reset()
       ctx.bot.send_chat_action(upd.message.chat.id, ChatAction.UPLOAD_PHOTO)
       res = ctx.chat_data["engine"].search(query, result_type)
    # Try to respond (while there are images left in the list)
    while attempts and len(res):
        ctx.bot.send_chat_action(upd.message.chat.id, ChatAction.UPLOAD_PHOTO)
        # Reset index if search type changed (precise <-> random)
        if search_type != ctx.chat_data["type"]:
            ctx.chat_data["index"].reset()
        # Set reply function - photo or animation
        reply_func = upd.message.reply_photo \
            if result_type == search.Picture \
            else upd.message.reply_animation
        # Get new image index
        index = ctx.chat_data["index"].set_next(search_type, len(res))
        logging.debug(f"Image link: {res[index].url}")
        # Reply or remove image if inaccessible
        try:
            reply_func(res[index].url)
        except:
            del res[index]
        else:
            break
    else:
        upd.message.reply_text("Nothing found")
    ctx.chat_data["type"] = search_type

def cmd_el_gato(upd: Update, ctx: CallbackContext, attempts=10):
    init_chat_data(ctx)
    res = ctx.chat_data["engine"].search_once("el gato +cat", search.Picture, num=10)
    attempts = 10
    while attempts and res:
        ctx.bot.send_chat_action(upd.message.chat.id, ChatAction.UPLOAD_PHOTO)
        index = randrange(len(res))
        logging.debug(f"El gato link: {res[index].url}")
        # Reply or remove image if inaccessible
        try:
            upd.message.reply_photo(res[index].url)
        except:
            del res[index]
        else:
            break

def add_handlers(d: Dispatcher):
    filter_ignorecase = lambda s: Filters.regex(re.compile(s, re.IGNORECASE))
    d.add_handler(MessageHandler(filter_ignorecase("^(дел|del)$"),                      cmd_del))
    d.add_handler(MessageHandler(filter_ignorecase("((/)?gato)|((/)?el_gato)|(el gato)"),     cmd_el_gato))
    d.add_handler(MessageHandler(filter_ignorecase("^(pls|плс)( .+)?$"),      lambda u, c: searcher(u, c, search.Picture,   search.Type.RANDOM)))
    d.add_handler(MessageHandler(filter_ignorecase("^(gif|гиф)( .+)?$"),      lambda u, c: searcher(u, c, search.Animation, search.Type.RANDOM)))
    d.add_handler(MessageHandler(filter_ignorecase("^(gif1|гиф1)( .+)?$"),    lambda u, c: searcher(u, c, search.Animation, search.Type.PRECISE)))
    d.add_handler(MessageHandler(filter_ignorecase("^(please|плис)( .+)?$"),  lambda u, c: searcher(u, c, search.Picture,   search.Type.PRECISE)))
    d.add_error_handler(lambda u, c: logging.error(c.error))


def main():
    init_logging()
    if is_local():
        init_env()
    updater = Updater(envar("TOKEN"), use_context=True)
    add_handlers(updater.dispatcher)
    start_bot(updater)


if __name__ == '__main__':
    main()