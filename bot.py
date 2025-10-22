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

def detect_faces_cv2(frame):
    """Tek karede yüzleri bulur (numpy array)"""
    ensure_cascade()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(CASCADE_PATH)
    faces = cascade.detectMultiScale(gray, 1.1, 5)
    return faces

def detect_faces(image):
    """PIL Image içinde yüzleri bulur"""
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    return detect_faces_cv2(img)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Fotoğraf veya video gönder, yüzleri sansürleyebilirim 🎭")

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

        draw = ImageDraw.Draw(img)
        for (x, y, w, h) in faces:
            draw.rectangle([x, y, x+w, y+h], fill="black")

        bio = BytesIO()
        img.save(bio, format="JPEG")
        bio.seek(0)
        await msg.reply_photo(photo=bio, caption=f"{len(faces)} yüz sansürlendi ✅")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    video = msg.video
    if not video:
        await msg.reply_text("Video alınamadı.")
        return

    await msg.reply_text("Videoda yüzler sansürleniyor, lütfen bekle... ⏳")

    with tempfile.TemporaryDirectory() as tmp:
        input_path = os.path.join(tmp, "input.mp4")
        output_path = os.path.join(tmp, "output.mp4")

        file = await video.get_file()
        await file.download_to_drive(custom_path=input_path)

        cap = cv2.VideoCapture(input_path)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_i = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            faces = detect_faces_cv2(frame)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 0), -1)

            out.write(frame)
            frame_i += 1
            if frame_i % int(fps * 2) == 0:  # her 2 saniyede bir ilerleme mesajı
                await msg.reply_chat_action("upload_video")

        cap.release()
        out.release()

        with open(output_path, "rb") as f:
            await msg.reply_video(video=f, caption="Yüzler sansürlendi 🎭")

async def error_handler(update, context):
    print(f"Hata: {context.error}")

def main():
    token = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_error_handler(error_handler)

    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
