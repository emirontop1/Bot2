import cv2
import numpy as np
from deepface import DeepFace
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from io import BytesIO
from PIL import Image
import tempfile

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba! Fotoğraf veya video gönder, yüzleri blur ile sansürleyebilirim 🎭"
    )

# ---------------- Fotoğraf ----------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    photo = msg.photo[-1]
    file = await photo.get_file()

    with tempfile.TemporaryDirectory() as tmp:
        path = f"{tmp}/photo.jpg"
        await file.download_to_drive(custom_path=path)

        img = cv2.imread(path)
        faces = DeepFace.detectFace(img, detector_backend='opencv', enforce_detection=False, align=False)

        # Eğer tek yüz döndüyse faces array değilse arraya çevir
        if faces.ndim == 1:
            faces = [faces]

        # Blur ile sansür
        for face in faces:
            x, y, w, h = face[0], face[1], face[2], face[3]
            x, y, w, h = int(x), int(y), int(w), int(h)
            roi = img[y:y+h, x:x+w]
            roi = cv2.GaussianBlur(roi, (51,51), 30)
            img[y:y+h, x:x+w] = roi

        bio = BytesIO()
        _, buf = cv2.imencode(".jpg", img)
        bio.write(buf)
        bio.seek(0)
        await msg.reply_photo(photo=bio, caption="Sansürlenmiş fotoğraf 🎭")

# ---------------- Video ----------------
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    video = msg.video
    if not video:
        await msg.reply_text("Video alınamadı.")
        return

    await msg.reply_text("Videoda yüzler sansürleniyor, lütfen bekle... ⏳")

    with tempfile.TemporaryDirectory() as tmp:
        input_path = f"{tmp}/input.mp4"
        output_path = f"{tmp}/output.mp4"
        file = await video.get_file()
        await file.download_to_drive(custom_path=input_path)

        cap = cv2.VideoCapture(input_path)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # DeepFace ile yüz algılama
            detections = DeepFace.extract_faces(frame, detector_backend='opencv', enforce_detection=False)
            for face_data in detections:
                x, y, w, h = face_data['facial_area'].values()
                roi = frame[y:y+h, x:x+w]
                roi = cv2.GaussianBlur(roi, (51,51), 30)
                frame[y:y+h, x:x+w] = roi

            out.write(frame)

        cap.release()
        out.release()

        with open(output_path, "rb") as f:
            await msg.reply_video(video=f, caption="Yüzler sansürlendi 🎭")

# ---------------- Bot ----------------
def main():
    token = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
