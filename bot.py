#!/usr/bin/env python3
"""
Telegram bot: fotoğraf alır, fotoğraftaki yüzleri tespit edip mozaikler, sonucu geri yollar.
Kullanım: TELEGRAM_TOKEN ortam değişkenini ayarla.
"""
import os
import logging
import tempfile
import requests
from io import BytesIO
from PIL import Image
import numpy as np
import cv2
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Haarcascade URL (otomatik indirilecek eğer yoksa)
CASCADE_URL = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
CASCADE_PATH = "haarcascade_frontalface_default.xml"


def ensure_cascade():
    if not os.path.exists(CASCADE_PATH):
        logger.info("Haarcascade bulunamadı, indiriliyor...")
        r = requests.get(CASCADE_URL, timeout=15)
        r.raise_for_status()
        with open(CASCADE_PATH, "wb") as f:
            f.write(r.content)
        logger.info("İndirildi: %s", CASCADE_PATH)
    else:
        logger.info("Haarcascade mevcut.")


def pixelate_region(img: np.ndarray, x, y, w, h, blocks=12):
    """
    Verilen görüntü (numpy) içindeki dikdörtgen bölgeyi bloklu mozaik yapar.
    blocks: mozaik yoğunluğu (daha az -> büyük blok -> daha çok sansür)
    """
    face = img[y:y+h, x:x+w]
    if face.size == 0:
        return img
    # küçük bir resmi tekrar büyütüp pixel effect
    (fh, fw) = (max(1, blocks), max(1, blocks))
    # resize down
    small = cv2.resize(face, (fw, fh), interpolation=cv2.INTER_LINEAR)
    # resize up to original face size (nearest for blocky look)
    pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    img[y:y+h, x:x+w] = pixelated
    return img


def censor_faces_pil(image_pil: Image.Image) -> Image.Image:
    """
    PIL Image alır, yüzleri tespit edip mozaik uygular, PIL Image döner.
    """
    # convert to OpenCV BGR
    img = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ensure_cascade()
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    logger.info("Tespit edilen yüz sayısı: %d", len(faces))
    for (x, y, w, h) in faces:
        # mozaik uygulamak için yüz bölgesini biraz genişletebiliriz:
        pad = int(0.15 * w)
        x0 = max(0, x - pad)
        y0 = max(0, y - pad)
        x1 = min(img.shape[1], x + w + pad)
        y1 = min(img.shape[0], y + h + pad)
        img = pixelate_region(img, x0, y0, x1 - x0, y1 - y0, blocks=12)

    # BGR -> RGB -> PIL
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)


# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba! Bana bir fotoğraf gönder, içindeki yüzleri sansürleyip geri göndereyim."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fotoğraf gönder: ben yüzleri mozaikleyip geri yollarım.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.photo:
        await msg.reply_text("Lütfen bir fotoğraf gönder.")
        return

    # En yüksek çözünürlüklü fotoğrafı seç
    photo = msg.photo[-1]
    file = await photo.get_file()
    logger.info("Dosya indiriliyor: %s", file.file_id)

    # Geçici dosyaya indir
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "input.jpg")
        await file.download_to_drive(custom_path=path)
        logger.info("İndirildi: %s", path)

        # Aç ve işle
        with Image.open(path) as im:
            # convert to RGB to avoid issues with PNG/CMYK
            im = im.convert("RGB")
            result = censor_faces_pil(im)

            out_path = os.path.join(tmpdir, "out.jpg")
            result.save(out_path, format="JPEG", quality=85)
            logger.info("İşlendi ve kaydedildi: %s", out_path)

            # Gönder
            with open(out_path, "rb") as f:
                await msg.reply_photo(photo=InputFile(f), caption="İşte sansürlenmiş fotoğrafın.")


async def handle_nonphoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bu bot sadece fotoğraf işliyor. Lütfen fotoğraf gönder.")


def main():
    token = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
    if not token:
        logger.error("TELEGRAM_TOKEN ortam değişkeni ayarlı değil.")
        raise SystemExit("Lütfen TELEGRAM_TOKEN ortam değişkenini ayarla.")

    # Ensure cascade exists early (download if gerekli)
    try:
        ensure_cascade()
    except Exception as e:
        logger.warning("Haarcascade indirme hatası: %s", e)

    # Create and run bot (python-telegram-bot v20+ style async)
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(~filters.PHOTO & filters.ALL, handle_nonphoto))

    logger.info("Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
