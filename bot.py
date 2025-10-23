from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Owner ID (sadece owner erişebilir)
OWNER_ID = 792398679  # Telegram ID'ni buraya koy

# /serv komutu
def serv_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        update.message.reply_text("Bu komut sadece owner için.")
        return

    chat = update.effective_chat
    info = (
        f"Chat Title: {chat.title}\n"
        f"Chat ID: {chat.id}\n"
        f"Type: {chat.type}\n"
        f"Members Count: {chat.get_members_count() if hasattr(chat, 'get_members_count') else 'Bilinmiyor'}"
    )
    update.message.reply_text(info)

def main():
    # TOKEN'ı .env dosyasından veya gizli config'ten al
    import os
    TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"

    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("serv", serv_command))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
