import os
import cv2
import numpy as np
import tempfile
import requests
from io import BytesIO
from PIL import Image, ImageDraw
from telegram import (
    Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

CASCADE_URL = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
CASCADE_PATH = "haarcascade_frontalface_default.xml"

def ensure_cascade():
    if not os.path.exists(CASCADE_PATH):
        r = requests.get(CASCADE_URL, timeout=15)
        r.raise_for_status()
        open(CASCADE_PATH, "wb").write(r.content)

def detect_faces(image: Image.Image):
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ensure_cascade()
    cascade = cv2.CascadeClassifier(CASCADE_PATH)
    faces = cascade.detectMultiScale(gray, 1.1, 5)
    return faces

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Fotoğraf gönder, yüzleri bulup sansürlemene yardımcı olayım.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    photo = msg.photo[-1]
    file = await photo.get_file()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "photo.jpg")
        await file.download_to_drive(custom_path=path)
        img = Image.open(path).convert("RGB")
        faces = detect_faces(img)
        if len(faces) == 0:
            await msg.reply_text("Yüz bulunamadı.")
            return

        # Kaydet data
        context.user_data["photo"] = img
        context.user_data["faces"] = faces
        context.user_data["selected"] = [False] * len(faces)

        await msg.reply_text(f"{len(faces)} yüz bulundu. Hangilerini sansürlemek istersin?")
        for i, (x, y, w, h) in enumerate(faces):
            face_crop = img.crop((x, y, x+w, y+h))
            bio = BytesIO()
            face_crop.save(bio, format="JPEG")
            bio.seek(0)
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🕶️ Sansürle", callback_data=f"toggle_{i}")]
            ])
            await msg.reply_photo(photo=bio, caption=f"Yüz #{i+1}", reply_markup=kb)
        await msg.reply_text("Tüm seçimleri yaptıysan 'Bitir' butonuna bas:", 
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Bitir", callback_data="finish")]]))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("toggle_"):
        idx = int(data.split("_")[1])
        context.user_data["selected"][idx] = not context.user_data["selected"][idx]
        status = "Sansürlenecek ✅" if context.user_data["selected"][idx] else "Sansürlenmeyecek ❌"
        await query.edit_message_caption(caption=f"Yüz #{idx+1} - {status}",
                                         reply_markup=query.message.reply_markup)
    elif data == "finish":
        img = context.user_data.get("photo")
        faces = context.user_data.get("faces", [])
        selected = context.user_data.get("selected", [])

        if not img or not faces:
            await query.message.reply_text("Önce bir fotoğraf gönder.")
            return

        result = img.copy()
        draw = ImageDraw.Draw(result)
        for (flag, (x, y, w, h)) in zip(selected, faces):
            if flag:
                draw.rectangle([x, y, x+w, y+h], fill="black")

        bio = BytesIO()
        result.save(bio, format="JPEG")
        bio.seek(0)
        await query.message.reply_photo(photo=bio, caption="Sansürlenmiş final görüntü 🎭")
        await query.message.reply_text("İşlem tamamlandı ✅")

def main():
    token = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
    if not token:
        raise SystemExit("TELEGRAM_TOKEN tanımlanmalı.")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
