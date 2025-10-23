from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import json
import os

TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
GROUPS_FILE = "groups.json"

# JSON dosyasını yükleme
def load_groups():
    if not os.path.exists(GROUPS_FILE):
        return set()
    try:
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            return set()
    except json.JSONDecodeError:
        return set()

# JSON dosyasına kaydetme
def save_groups(groups):
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(groups), f, indent=4)

groups = load_groups()

# Komut: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    groups.add(chat_id)
    save_groups(groups)
    await update.message.reply_text("Merhaba! Bot aktif ve gruba eklendin.")

# Komut: /groups
async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Botun bulunduğu gruplar: {len(groups)}")

# Mesaj geldiğinde
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Mesaj aldım: {update.message.text}")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("groups", list_groups))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

app.run_polling()
