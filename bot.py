from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import asyncio

OWNER_ID = 792398679  # Telegram ID
active_chats = {}

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
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

async def start_bot(context: ContextTypes.DEFAULT_TYPE):
    # Bot eklendiği tüm chatlerde başlangıç mesajı gönderir ve kaydeder
    for chat_id in list(active_chats.keys()):
        try:
            await context.bot.send_message(chat_id=chat_id, text="Bot aktif ve kaydedildi!")
        except:
            pass

def main():
    TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
    app = ApplicationBuilder().token(TOKEN).build()

    # Tüm mesajları yakalayıp chatleri kaydet
    app.add_handler(MessageHandler(filters.ALL, track_chats))
    app.add_handler(CommandHandler("serv", serv_command))

    # Bot başlatıldığında start_bot fonksiyonunu çalıştır
    app.job_queue.run_once(start_bot, 1)

    app.run_polling()

if __name__ == "__main__":
    main()
