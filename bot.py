import os
import re
import io
from PIL import Image
import numpy as np
import easyocr
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image as keras_image
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Load OCR and classifier once
OCR_READER = easyocr.Reader(['en'])  # hızlı başlamak için İngilizce; ek diller ekleyebilirsin
CLASSIFIER = MobileNetV2(weights='imagenet')

TELEGRAM_TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"

if not TELEGRAM_TOKEN:
    raise RuntimeError("Environment variable TELEGRAM_TOKEN gerekli.")

# Basit plaka regex: rakam ve harf karışımı 4-10 uzunluk
PLATE_REGEX = re.compile(r'([A-Z0-9\-]{4,12})', re.IGNORECASE)

def pil_from_bytes(b: bytes) -> Image.Image:
    return Image.open(io.BytesIO(b)).convert('RGB')

def detect_plate_text(pil_img: Image.Image) -> str:
    # easyocr expects numpy array
    arr = np.array(pil_img)
    results = OCR_READER.readtext(arr, detail=0)
    # join results and search for plausible plate-like tokens
    joined = " ".join(results)
    candidates = PLATE_REGEX.findall(joined)
    # choose longest candidate (heuristic)
    if candidates:
        candidates = sorted(set(candidates), key=lambda s: (-len(s), s))
        return candidates[0].upper()
    return ""

def predict_car_model(pil_img: Image.Image, top_n=3) -> list:
    # Resize to MobileNetV2 expected input
    img = pil_img.resize((224,224))
    x = keras_image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    preds = CLASSIFIER.predict(x)
    decoded = decode_predictions(preds, top=top_n)[0]
    # return list of (label, description, score) simplified
    return [(item[0], item[1].replace('_', ' '), float(item[2])) for item in decoded]

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.photo:
            await update.message.reply_text("Fotoğraf göndermedim.")
            return
        # en yüksek çözünürlüklü fotoğrafı al
        file = await update.message.photo[-1].get_file()
        bio = io.BytesIO()
        await file.download(out=bio)
        bio.seek(0)
        pil = pil_from_bytes(bio.read())

        # Plaka tespiti
        plate = detect_plate_text(pil)

        # Model tahmini (approx)
        preds = predict_car_model(pil, top_n=3)
        pred_text = "\n".join([f"{i+1}. {p[1]} ({p[2]*100:.1f}%)" for i,p in enumerate(preds)])

        # Yanıtı oluştur
        reply = []
        if plate:
            reply.append(f"Plaka (tahmini): {plate}")
        else:
            reply.append("Plaka bulunamadı.")

        reply.append("Araba modeli (yaklaşık tahminler):")
        reply.append(pred_text)

        await update.message.reply_text("\n".join(reply))
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")

async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fotoğraf gönderirsen plaka ve model tahmini yaparım.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(~filters.PHOTO, handle_other))
    # Long polling. Railway çalıştırır.
    app.run_polling()

if __name__ == "__main__":
    main()
