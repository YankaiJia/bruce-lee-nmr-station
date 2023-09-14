"""
This code will read the last n lines of the main.log file and
send it to the telegram bot when the bot is requested with the '/s' command.
"""

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram import InlineQueryResultArticle, InputTextMessageContent

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

# return the last n lines of a file
def tail(f, lines):
    total_lines_wanted = lines

    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = []
    while lines_to_go > 0 and block_end_byte > 0:
        if (block_end_byte - BLOCK_SIZE > 0):
            f.seek(block_number * BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            f.seek(0, 0)
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count(b'\n')
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = b''.join(reversed(blocks))
    return b'\n'.join(all_read_text.splitlines()[-total_lines_wanted:])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open('../logs/main.log', 'rb') as f:
        last_lines = tail(f, 10).decode()

    await context.bot.send_message(chat_id=update.effective_chat.id, text=last_lines)

if __name__ == '__main__':
    with open('token_DO_NOT_COMMIT.txt') as f:
        for line in f:
            token_robo = line
    application = ApplicationBuilder().token(token_robo).build()
    start_handler = CommandHandler('s', start)
    application.add_handler(start_handler)

    application.run_polling()