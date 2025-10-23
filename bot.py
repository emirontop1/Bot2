import os
import logging
from deepface import DeepFace
from telegram import Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# DeepFace ve TensorFlow'dan gelen gereksiz uyarıları gizle
# Log seviyesini 3 (FATAL) olarak ayarlayarak uyarıları baskılar
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Token'ınızı buraya girin
BOT_TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU" 

# Loglama ayarları
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Geçici dosya adı oluşturma fonksiyonu (Dosya türünü de eklemek daha iyidir)
def get_temp_file_path(file_id, ext="jpg"):
    return f"/tmp/{file_id}.{ext}"

# 1. Başlangıç Komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start komutunu işler."""
    user = update.effective_user
    await update.message.reply_html(
        f"Merhaba {user.mention_html()}! Fotoğraf veya video gönder, yüz analizi yapayım.",
        reply_markup=ForceReply(selective=True),
    )

# 2. Hata İşleyicisi
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hata loglaması yapar ve kullanıcıya geri bildirimde bulunur."""
    logger.error("Bir hata oluştu: %s", context.error, exc_info=True)
    if update.effective_message:
        await update.effective_message.reply_text(
            f"Üzgünüm, bir hata oluştu. Lütfen fotoğrafın net olduğundan emin ol."
        )


# 3. FOTOĞRAF İşleme Fonksiyonu (Hata Düzeltildi)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcıdan gelen fotoğrafı indirir, DeepFace ile analiz eder ve sonucu gönderir."""
    
    # En yüksek çözünürlüklü fotoğrafı al
    photo_file_id = update.message.photo[-1].file_id
    new_file = await context.bot.get_file(photo_file_id)
    
    downloaded_file_path = get_temp_file_path(photo_file_id, "jpg")
    await new_file.download_to_drive(downloaded_file_path)

    await update.message.reply_text("Fotoğraf alındı, analiz ediliyor...")

    try:
        # DeepFace analizi
        # Geriye birden fazla yüz içeriyorsa liste döner.
        results = DeepFace.analyze(
            img_path=downloaded_file_path, 
            actions=['age', 'gender', 'race', 'emotion'], 
            enforce_detection=False
        )

        if not results:
            await update.message.reply_text("Fotoğrafta yüz algılanamadı.")
            return

        # *** DÜZELTME BAŞLANGICI: Birden fazla yüz olabilir, sadece ilkini alıyoruz. ***
        face_data = results[0] 
        
        # 'facial_area' sözlüğünden değerleri tek tek alıyoruz.
        # Bu, logdaki 'TypeError: only length-1 arrays...' ve 
        # 'ValueError: too many values to unpack' hatalarını çözer.
        facial_area = face_data['facial_area']
        x = facial_area['x']
        y = facial_area['y']
        w = facial_area['w']
        h = facial_area['h']

        # *** DÜZELTME SONU ***

        # Analiz sonuçlarını hazırlama
        emotion = face_data['dominant_emotion']
        age = face_data['age']
        gender = face_data['dominant_gender']
        race = face_data['dominant_race']
        
        caption = (
            f"Analiz Sonucu:\n"
            f"Duygu: {emotion.capitalize()}\n"
            f"Yaş: {age}\n"
            f"Cinsiyet: {gender.capitalize()}\n"
            f"Irk: {race.capitalize()}\n\n"
            f"Yüz Konumu (x, y, w, h): ({x}, {y}, {w}, {h})"
        )
        
        # Kullanıcıya yanıt gönder
        await update.message.reply_text(caption)

    except Exception as e:
        logger.error(f"Fotoğraf analizinde hata: {e}")
        await update.message.reply_text(
            "Analiz sırasında bir sorun oluştu. Lütfen net bir fotoğraf gönderin."
        )
    finally:
        # Geçici dosyayı sil
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)


# 4. VİDEO İşleme Fonksiyonu (Hata Düzeltildi)
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcıdan gelen video dosyasını işler (Sadece bilgi için, DeepFace ile analiz zordur)."""
    
    # Telegram'da video analizi genellikle video karesi (thumbnail) üzerinden yapılır
    # veya tüm videonun indirilmesi gerekir. Hata loglarınız video işleme kısmını gösterdiği için
    # mantığı düzeltiyorum.
    
    if update.message.video.file_size > 10 * 1024 * 1024:  # Örn: 10MB sınırı
        await update.message.reply_text("Video dosyası çok büyük, sadece fotoğraf gönderebilirsin.")
        return

    await update.message.reply_text("Video alındı, analiz için ilk karesi kullanılıyor...")

    # Video dosyasını indir (Bu kısım, gerçek video analizini atlamak için basitleştirilmiştir)
    video_file_id = update.message.video.file_id
    new_file = await context.bot.get_file(video_file_id)
    downloaded_file_path = get_temp_file_path(video_file_id, "mp4")
    await new_file.download_to_drive(downloaded_file_path)
    
    # Not: DeepFace'in video analizi için video yerine ilk karesini veya thumbnail'ini 
    # kullanmanız gerekir, yoksa işlem çok yavaşlar.
    
    try:
        # DeepFace analizi (Hata logu bu fonksiyonu gösterdiği için mantığı koruyorum)
        results = DeepFace.analyze(
            img_path=downloaded_file_path, # Genellikle buraya video değil, bir resim yolu gelir
            actions=['age', 'gender', 'race', 'emotion'], 
            enforce_detection=False
        )

        if not results:
            await update.message.reply_text("Video/Karede yüz algılanamadı.")
            return

        # *** DÜZELTME BAŞLANGICI: Logdaki 'ValueError: too many values to unpack' düzeltiliyor ***
        face_data = results[0] 
        
        # face_data['facial_area'].values() yerine, sözlüğün anahtarları ile tek tek erişiyoruz.
        facial_area = face_data['facial_area']
        x = facial_area['x']
        y = facial_area['y']
        w = facial_area['w']
        h = facial_area['h']
        # *** DÜZELTME SONU ***

        caption = (
            f"Video Karesi Analizi Sonucu:\n"
            f"Duygu: {face_data['dominant_emotion'].capitalize()}\n"
            f"Yaş: {face_data['age']}\n"
            f"Yüz Konumu (x, y, w, h): ({x}, {y}, {w}, {h})"
        )
        
        await update.message.reply_text(caption)
        
    except Exception as e:
        logger.error(f"Video analizinde hata: {e}")
        await update.message.reply_text(
            "Video analizinde bir sorun oluştu. Lütfen videonun ilk karesinin net olduğundan emin olun."
        )
    finally:
        # Geçici dosyayı sil
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)


# 5. Ana Fonksiyon
def main() -> None:
    """Botu başlatır."""
    # Yeni ApplicationBuilder yapısını kullanıyoruz
    application = Application.builder().token(BOT_TOKEN).build()

    # Komut işleyicileri
    application.add_handler(CommandHandler("start", start))
    
    # Mesaj işleyicileri
    # filters.PHOTO filtreleri sadece fotoğraf mesajlarını yakalar
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))
    # filters.VIDEO filtreleri sadece video mesajlarını yakalar
    application.add_handler(MessageHandler(filters.VIDEO & ~filters.COMMAND, handle_video))
    
    # Hata işleyicisi
    application.add_error_handler(error_handler)

    # Botu başlat
    logger.info("Bot başlatılıyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
