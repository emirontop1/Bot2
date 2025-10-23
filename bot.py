from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

OWNER_USERNAME = "DincEMR"  # sadece owner komutu çalıştırabilir


async def serverst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Sadece owner çalıştırabilir
    if user.username != OWNER_USERNAME:
        await update.message.reply_text("Bu komutu sadece owner kullanabilir.")
        return

    bot = context.bot

    try:
        # Güncellemeleri al
        chat_list = await bot.get_updates()
        group_names = set()

        # Botun bulunduğu grupları bul
        for update_item in chat_list:
            chat = getattr(update_item.message, "chat", None)
            if chat and chat.type in ["group", "supergroup"]:
                group_names.add(chat.title)

        # Hiç grup bulunmadıysa
        if not group_names:
            await update.message.reply_text("Bot şu anda hiçbir grupta değil.")
            return

        # Mesaj oluştur
        msg = "📋 Botun bulunduğu gruplar:\n\n" + "\n".join(f"- {name}" for name in group_names)
        sent_msg = await update.message.reply_text(msg)

        # Mesajı silmeyi dene
        try:
            await sent_msg.delete()
        except Exception as e:
            error_message = str(e)
            if "message can't be deleted" in error_message or "not an administrator" in error_message:
                print("Uyarı: Bot mesajı silemedi (yetki eksikliği).")
            else:
                raise  # farklı bir hata varsa durdur

    except Exception as e:
        await update.message.reply_text(f"Bir hata oluştu: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token("8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU").build()
    app.add_handler(CommandHandler("serverst", serverst))
    app.run_polling()
