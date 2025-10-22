import os
import cv2
import numpy as np
from mtcnn import MTCNN
from retinaface import RetinaFace
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"  # Railway'de çevre değişkeni olarak ayarla: BOT_TOKEN

# --- Yüz Algılama ---
def detect_faces(img):
    faces = []

    # 1️⃣ RetinaFace
    try:
        detections = RetinaFace.detect_faces(img)
        if isinstance(detections, dict):
            for key in detections:
                facial_area = detections[key]["facial_area"]
                faces.append(facial_area)
    except Exception as e:
        print("RetinaFace hata:", e)

    # 2️⃣ MTCNN fallback
    if len(faces) == 0:
        try:
            detector = MTCNN()
            results = detector.detect_faces(img)
            for res in results:
                x, y, w, h = res["box"]
                faces.append([x, y, x + w, y + h])
        except Exception as e:
            print("MTCNN hata:", e)

    # 3️⃣ Cascade fallback
    if len(faces) == 0:
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            results = cascade.detectMultiScale(gray, 1.1, 4)
            for (x, y, w, h) in results:
                faces.append([x, y, x + w, y + h])
        except Exception as e:
            print("Cascade hata:", e)

    return faces


# --- Sansürleme ---
def censor_faces(img, faces_to_censor):
    censored = img.copy()
    for (x1, y1, x2, y2) in faces_to_censor:
        cv2.rectangle(censored, (x1, y1), (x2, y2), (0, 0, 0), -1)
    return censored


# --- Bellekte kullanıcı verisi ---
user_photos = {}  # {user_id: {"img": np.array, "faces": [[x1,y1,x2,y2]]}}


# --- Komut: /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Merhaba! Fotoğraf gönder, yüzleri bulup sansürleyelim.")


# --- Fotoğraf Alındığında ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = await file.download_as_bytearray()

    # OpenCV’ye çevir
    np_arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    faces = detect_faces(img)

    if len(faces) == 0:
        await update.message.reply_text("😕 Yüz bulunamadı.")
        return

    user_id = update.message.from_user.id
    user_photos[user_id] = {"img": img, "faces": faces}

    # Her yüz için küçük önizleme oluştur
    previews = []
    keyboard = []
    for i, (x1, y1, x2, y2) in enumerate(faces):
        crop = img[y1:y2, x1:x2]
        _, buffer = cv2.imencode(".jpg", crop)
        previews.append(buffer.tobytes())
        keyboard.append([InlineKeyboardButton(f"Sansürle #{i+1}", callback_data=f"censor_{i}")])

    keyboard.append([InlineKeyboardButton("✅ Bitir ve Sansürle", callback_data="finish")])

    await update.message.reply_text("📷 Şu kişileri buldum! Hangilerini sansürlemek istersin?",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

    for p in previews:
        await update.message.reply_photo(photo=p)


# --- Buton İşlemleri ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    data = query.data
    if user_id not in user_photos:
        await query.edit_message_text("Lütfen önce bir fotoğraf gönder.")
        return

    info = user_photos[user_id]
    if "selected" not in info:
        info["selected"] = []

    if data.startswith("censor_"):
        idx = int(data.split("_")[1])
        if idx not in info["selected"]:
            info["selected"].append(idx)
        await query.edit_message_text(f"✅ #{idx+1} yüzü sansür listesine eklendi. İstersen diğerlerini de seç.")
    elif data == "finish":
        img = info["img"]
        selected = [info["faces"][i] for i in info.get("selected", [])]
        result = censor_faces(img, selected)

        _, buffer = cv2.imencode(".jpg", result)
        await query.message.reply_photo(photo=BytesIO(buffer.tobytes()))
        await query.message.reply_text("🎉 Sansür tamamlandı!")
        del user_photos[user_id]


# --- Uygulama Başlat ---
if __name__ == "__main__":
    print("🚀 Bot çalışıyor...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()
