from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
registered_groups = {}  # {user_id: {chat_id: [cursed_words]}}

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Bu komut sadece gruplarda kullanılabilir.")
        return
    registered_groups.setdefault(user_id, {}).setdefault(chat.id, [])
    await update.message.reply_text(f"Grup kaydedildi: {chat.title}")

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    groups = registered_groups.get(user_id, {})
    if not groups:
        await update.message.reply_text("Hiç kayıtlı grubunuz yok.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{chat_id}", callback_data=f"group_{chat_id}")]
        for chat_id in groups
    ]
    await update.message.reply_text("Grup paneli:", reply_markup=InlineKeyboardMarkup(keyboard))

async def group_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = int(query.data.split("_")[1])
    keyboard = [
        [InlineKeyboardButton("Cursed Ekle", callback_data=f"add_{chat_id}")],
        [InlineKeyboardButton("Cursed Sil", callback_data=f"del_{chat_id}")],
        [InlineKeyboardButton("Görüntüle", callback_data=f"view_{chat_id}")]
    ]
    await query.edit_message_text("İşlem seçin:", reply_markup=InlineKeyboardMarkup(keyboard))

async def cursed_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action, chat_id = query.data.split("_")
    chat_id = int(chat_id)
    if action == "view":
        words = registered_groups[user_id].get(chat_id, [])
        await query.edit_message_text(f"Cursed kelimeler: {', '.join(words) if words else 'yok'}")
    elif action == "add":
        await query.edit_message_text("Yeni cursed kelime eklemek için mesaj atın:")
        context.user_data['add_cursed_chat'] = chat_id
    elif action == "del":
        await query.edit_message_text("Silmek istediğiniz cursed kelimeyi mesaj olarak atın:")
        context.user_data['del_cursed_chat'] = chat_id

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    # Panel için kelime ekleme/silme
    if 'add_cursed_chat' in context.user_data:
        chat_id = context.user_data.pop('add_cursed_chat')
        registered_groups[user_id][chat_id].append(text)
        await update.message.reply_text(f"'{text}' eklendi.")
        return
    if 'del_cursed_chat' in context.user_data:
        chat_id = context.user_data.pop('del_cursed_chat')
        if text in registered_groups[user_id][chat_id]:
            registered_groups[user_id][chat_id].remove(text)
            await update.message.reply_text(f"'{text}' silindi.")
        else:
            await update.message.reply_text(f"'{text}' listede yok.")
        return

    # Cursed kelime kontrolü
    for owner_id, groups in registered_groups.items():
        for chat_id, words in groups.items():
            if chat_id == update.effective_chat.id:
                for word in words:
                    if word in text:
                        try:
                            await update.message.delete()
                        except:
                            pass
                        await context.bot.send_message(chat_id=update.effective_user.id,
                                                       text=f"Mesajınız silindi: '{word}' içeriyor.")
                        return

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CallbackQueryHandler(group_panel, pattern="^group_"))
    app.add_handler(CallbackQueryHandler(cursed_action, pattern="^(add|del|view)_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
