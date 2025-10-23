from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from deepface import DeepFace
import io
from PIL import Image
import os

TELEGRAM_TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
if not TELEGRAM_TOKEN:
    raise RuntimeError("Environment variable TELEGRAM_TOKEN gerekli.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.photo:
            await update.message.reply_text("Fotoğraf göndermedim.")
            return

        # Fotoğrafı al
        file = await update.message.photo[-1].get_file()
        bio = io.BytesIO()
        await file.download(out=bio)
        bio.seek(0)
        pil_img = Image.open(bio).convert("RGB")
        
        # DeepFace analiz
        analysis = DeepFace.analyze(np.array(pil_img), actions=["age", "gender", "emotion", "race"], enforce_detection=False)
        
        reply = f"""
Yaş: {analysis['age']}
Cinsiyet: {analysis['gender']}
Duygu: {analysis['dominant_emotion']}
Irk: {analysis['dominant_race']}
"""
        await update.message.reply_text(reply.strip())
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")

async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fotoğraf gönderirsen yüz analizi yapabilirim.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(~filters.PHOTO, handle_other))
    app.run_polling()

if __name__ == "__main__":
    main()
