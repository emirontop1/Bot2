from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

OWNER_ID = 792398679  # Telegram ID'ni buraya koy

async def serv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("Bu komut sadece owner için.")
        return

    chat = update.effective_chat
    info = (
        f"Chat Title: {chat.title}\n"
        f"Chat ID: {chat.id}\n"
        f"Type: {chat.type}"
    )
    await update.message.reply_text(info)

def main():
    TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"  # .env veya ortam değişkeninden al
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("serv", serv_command))

    app.run_polling()

if __name__ == "__main__":
    main()
