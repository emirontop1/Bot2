from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"

# Kayıtlı gruplar: {user_id: [chat_id, ...]}
registered_groups = {}

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat

    if chat.type in ["group", "supergroup"]:
        if user_id not in registered_groups:
            registered_groups[user_id] = []
        if chat.id not in registered_groups[user_id]:
            registered_groups[user_id].append(chat.id)
        await update.message.reply_text(f"Grup kaydedildi: {chat.title}")
    else:
        await update.message.reply_text("Bu komut sadece gruplarda kullanılabilir.")

async def myserv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    groups = registered_groups.get(user_id, [])
    if not groups:
        await update.message.reply_text("Hiç kayıtlı grubunuz yok.")
        return

    text = "Kayıtlı gruplarınız:\n"
    for chat_id in groups:
        text += f"- {chat_id}\n"
    await update.message.reply_text(text)

async def cursed_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "merhaba mal" in text:
        try:
            await update.message.delete()
        except:
            pass
        await context.bot.send_message(chat_id=update.effective_user.id, text="Bu mesaj silindi: 'merhaba mal'")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("myserv", myserv))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), cursed_filter))

    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
