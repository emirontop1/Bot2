import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, ChatMemberHandler
)

OWNER_USERNAME = "DincEMR"
DATA_FILE = "joined_groups.json"


# Dosyadan grupları yükle
def load_groups():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()


# Grupları dosyaya kaydet
def save_groups(groups):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(groups), f, ensure_ascii=False, indent=2)


joined_groups = load_groups()


# Bot bir gruba eklendiğinde veya kaldırıldığında çalışır
async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.chat
    if chat and chat.type in ["group", "supergroup"]:
        joined_groups.add(chat.title)
        save_groups(joined_groups)


# /serverst komutu
async def serverst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != OWNER_USERNAME:
        await update.message.reply_text("Bu komutu sadece owner kullanabilir.")
        return

    if not joined_groups:
        await update.message.reply_text("Bot şu anda hiçbir grupta değil.")
        return

    msg = "📋 Botun bulunduğu gruplar:\n\n" + "\n".join(f"- {name}" for name in joined_groups)
    sent_msg = await update.message.reply_text(msg)

    try:
        await sent_msg.delete()
    except Exception as e:
        err = str(e)
        if "message can't be deleted" in err or "not an administrator" in err:
            print("Uyarı: Mesaj silme yetkisi yok.")
        else:
            raise


if __name__ == "__main__":
    app = ApplicationBuilder().token("8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU").build()
    app.add_handler(ChatMemberHandler(track_groups, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("serverst", serverst))
    app.run_polling()
