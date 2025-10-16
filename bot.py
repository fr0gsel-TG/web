import logging
from telegram import Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot's token
TOKEN = "7724093672:AAFnWkmxXRm6Thd0UalWtL-s9HIKW08X8Ho"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with a button that opens the web app."""
    await update.message.reply_text(
        "Welcome to TonStore!",
        reply_markup={"inline_keyboard": [[{"text": "Open Store", "web_app": {"url": "https://web-9jub0gzbo-fr0gsel1s-projects.vercel.app/"}}]]}
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes data from the web app."""
    data = update.message.web_app_data.data
    await update.message.reply_text(f"You have selected: {data}")

def main() -> None:
    """Start the bot."""
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

    application.run_polling()

if __name__ == "__main__":
    main()
