import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

OWNER_ID = 792398679  # Telegram ID
banned_words = {}  # {chat_id: [word1, word2]}

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
    if chat.id not in banned_words:
        banned_words[chat.id] = []

async def myserv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("Bu komut sadece owner için.")
        return
    response = "Sahip olduğun chatler:\n"
    for chat_id, words in banned_words.items():
        chat = await context.bot.get_chat(chat_id)
        if chat.get_member(OWNER_ID).status in ["creator", "administrator"]:
            response += f"Name: {chat.title or chat.first_name}\nID: {chat_id}\n---\n"
    await update.message.reply_text(response)

async def add_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if context.args:
        word = context.args[0].lower()
        banned_words.setdefault(chat_id, []).append(word)
        await update.message.reply_text(f"'{word}' kelimesi yasaklandı.")
    else:
        await update.message.reply_text("Kelime yazmalısın.")

async def remove_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if context.args:
        word = context.args[0].lower()
        if chat_id in banned_words and word in banned_words[chat_id]:
            banned_words[chat_id].remove(word)
            await update.message.reply_text(f"'{word}' yasaklı listeden çıkarıldı.")
        else:
            await update.message.reply_text("Kelime bulunamadı.")
    else:
        await update.message.reply_text("Kelime yazmalısın.")

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    msg = update.message.text.lower()
    for word in banned_words.get(chat_id, []):
        if word in msg:
            await update.message.delete()
            await update.effective_user.send_message(f"Mesajın silindi çünkü '{word}' yasaklı.")
            break

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif!")

if __name__ == "__main__":
    TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myserv", myserv))
    app.add_handler(CommandHandler("ban_add", add_banned))
    app.add_handler(CommandHandler("ban_remove", remove_banned))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))
    app.add_handler(MessageHandler(filters.ALL, track_chats))

    app.run_polling()
