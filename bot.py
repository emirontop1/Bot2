from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"

# Kayıtlı gruplar ve cursed listeleri
# {user_id: {chat_id: [cursed_words]}}
registered_groups = {}

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat

    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Bu komut sadece gruplarda kullanılabilir.")
        return

    if user_id not in registered_groups:
        registered_groups[user_id] = {}
    if chat.id not in registered_groups[user_id]:
        registered_groups[user_id][chat.id] = []
    await update.message.reply_text(f"Grup kaydedildi: {chat.title}")

async def myserv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    groups = registered_groups.get(user_id, {})
    if not groups:
        await update.message.reply_text("Hiç kayıtlı grubunuz yok.")
        return

    text = "Sahip olduğunuz gruplar:\n"
    for chat_id in groups:
        text += f"- {chat_id}, Cursed kelimeler: {', '.join(groups[chat_id]) or 'yok'}\n"
    await update.message.reply_text(text)

async def addcursed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat
    if len(context.args) == 0:
        await update.message.reply_text("Kullanım: /addcursed <kelime>")
        return
    word = context.args[0].lower()

    if user_id not in registered_groups or chat.id not in registered_groups[user_id]:
        await update.message.reply_text("Önce /register ile grubu kaydedin.")
        return

    if word not in registered_groups[user_id][chat.id]:
        registered_groups[user_id][chat.id].append(word)
        await update.message.reply_text(f"'{word}' cursed listesine eklendi.")

async def delcursed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat
    if len(context.args) == 0:
        await update.message.reply_text("Kullanım: /delcursed <kelime>")
        return
    word = context.args[0].lower()

    if user_id not in registered_groups or chat.id not in registered_groups[user_id]:
        await update.message.reply_text("Önce /register ile grubu kaydedin.")
        return

    if word in registered_groups[user_id][chat.id]:
        registered_groups[user_id][chat.id].remove(word)
        await update.message.reply_text(f"'{word}' cursed listesinden silindi.")
    else:
        await update.message.reply_text(f"'{word}' cursed listesinde yok.")

async def cursed_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.lower()

    for owner_id, groups in registered_groups.items():
        if chat_id in groups:
            for word in groups[chat_id]:
                if word in text:
                    try:
                        await update.message.delete()
                    except:
                        pass
                    await context.bot.send_message(
                        chat_id=update.effective_user.id,
                        text=f"Mesajınız silindi: '{word}' içeriyor."
                    )
                    return

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("myserv", myserv))
    app.add_handler(CommandHandler("addcursed", addcursed))
    app.add_handler(CommandHandler("delcursed", delcursed))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), cursed_filter))

    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
