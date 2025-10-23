from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

OWNER_ID = 792398679  # Telegram ID'ni buraya koy

# Aktif chat bilgilerini tutmak için dict
active_chats = {}

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    # chat tipine göre kaydet (grup, kanal, bireysel)
    active_chats[chat.id] = {
        "title": chat.title or "Bireysel Chat",
        "type": chat.type,
        "owner": chat.get_member(context.bot.id).user.full_name if chat.type != "private" else update.effective_user.full_name,
        "members_count": getattr(chat, 'get_members_count', lambda: 'Bilinmiyor')()
    }

async def serv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Bu komut sadece owner için.")
        return

    if not active_chats:
        await update.message.reply_text("Henüz aktif chat yok.")
        return

    response = "Botun aktif olduğu chatler:\n\n"
    for chat_id, info in active_chats.items():
        response += (
            f"Name: {info['title']}\n"
            f"Type: {info['type']}\n"
            f"Owner/Bot: {info['owner']}\n"
            f"Members: {info['members_count']}\n"
            f"---\n"
        )
    await update.message.reply_text(response)

def main():
    TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
    app = ApplicationBuilder().token(TOKEN).build()

    # Her mesajda chat kaydı
    app.add_handler(CommandHandler("start", track_chats))
    app.add_handler(CommandHandler("serv", serv_command))
    # Alternatif olarak tüm mesajları yakalamak için MessageHandler eklenebilir

    app.run_polling()

if __name__ == "__main__":
    main()
