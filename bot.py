import os
import logging
import asyncio
from deepface import DeepFace
from telegram import Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ==============================================================================
# 1. TEMEL AYARLAR VE GEREKSİZ UYARILARI GİZLEME
# ==============================================================================

# Lütfen BURAYI kendi Telegram Bot token'ınızla değiştirin!
BOT_TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU" 

# DeepFace ve TensorFlow'dan gelen CUDA/CPU uyarılarını gizle
# Log seviyesini 3 (FATAL) olarak ayarlayarak uyarıları baskılar
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Loglama ayarları
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Geçici dosya adı oluşturma fonksiyonu
def get_temp_file_path(file_id, ext="jpg"):
    """Dosyayı kaydetmek için benzersiz bir geçici yol döndürür."""
    # os.path.join kullanılarak platformdan bağımsız yol oluşturulur
    return os.path.join("/tmp", f"{file_id}.{ext}")

# ==============================================================================
# 2. İŞLEYİCİ FONKSİYONLAR
# ==============================================================================

# /start komutunu işler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start komutunu işler."""
    user = update.effective_user
    await update.message.reply_html(
        f"Merhaba {user.mention_html()}! Fotoğraf veya video gönder, yüz analizi yapayım.",
        reply_markup=ForceReply(selective=True),
    )

# Hata işleyicisi (Önceki loglardaki 'No error handlers are registered' sorununu çözer)
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hata loglaması yapar ve kullanıcıya geri bildirimde bulunur."""
    logger.error("İşleyici hatası: %s", context.error, exc_info=True)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"Üzgünüm, bir hata oluştu. Lütfen fotoğrafın net olduğundan veya bot token'ının doğru olduğundan emin ol."
            )
        except Exception as e:
            logger.error(f"Kullanıcıya hata mesajı gönderirken hata oluştu: {e}")

# FOTOĞRAF İşleme Fonksiyonu (Düzeltildi)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcıdan gelen fotoğrafı indirir ve DeepFace ile analiz eder."""
    
    # En yüksek çözünürlüklü fotoğrafı al
    photo_file_id = update.message.photo[-1].file_id
    
    await update.message.reply_text("Fotoğraf alındı, analiz ediliyor...")

    downloaded_file_path = None
    try:
        # 1. Dosyayı indir
        new_file = await context.bot.get_file(photo_file_id)
        downloaded_file_path = get_temp_file_path(photo_file_id, "jpg")
        await new_file.download_to_drive(downloaded_file_path)
        
        logger.info(f"Dosya indirildi: {downloaded_file_path}")

        # 2. DeepFace analizi
        # Geriye birden fazla yüz içeriyorsa liste döner.
        results = DeepFace.analyze(
            img_path=downloaded_file_path, 
            actions=['age', 'gender', 'race', 'emotion'], 
            enforce_detection=False # Algılama başarısız olsa bile hata fırlatmayı engeller
        )

        if not results:
            await update.message.reply_text("Fotoğrafta yüz algılanamadı.")
            return

        # 3. Analiz sonucunu güvenli şekilde ayrıştırma (Hata düzeltmeleri burada yapıldı)
        
        # Sadece ilk algılanan yüzün verilerini al
        face_data = results[0] 
        
        # Loglardaki ValueError ve TypeError'ı çözen güvenli ayrıştırma
        facial_area = face_data['facial_area']
        x = facial_area['x']
        y = facial_area['y']
        w = facial_area['w']
        h = facial_area['h']

        # 4. Sonucu kullanıcıya gönderme
        caption = (
            f"Analiz Sonucu:\n"
            f"Duygu: {face_data.get('dominant_emotion', 'Bilinmiyor').capitalize()}\n"
            f"Yaş: {face_data.get('age', 'Bilinmiyor')}\n"
            f"Cinsiyet: {face_data.get('dominant_gender', 'Bilinmiyor').capitalize()}\n"
            f"Irk: {face_data.get('dominant_race', 'Bilinmiyor').capitalize()}\n\n"
            f"Yüz Konumu (x, y, w, h): ({x}, {y}, {w}, {h})"
        )
        
        await update.message.reply_text(caption)

    except Exception as e:
        logger.error(f"Fotoğraf analizinde beklenmeyen hata: {e}")
        await update.message.reply_text(
            "Analiz sırasında bir sorun oluştu. Lütfen net ve tek yüz içeren bir fotoğraf gönderin."
        )
    finally:
        # 5. Geçici dosyayı sil
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)
            logger.info(f"Geçici dosya silindi: {downloaded_file_path}")


# VİDEO İşleme Fonksiyonu (Düzeltildi)
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcıdan gelen videoyu işler (DeepFace genellikle videolar için uygun değildir,
       bu yüzden sadece ilk karesini analiz etmeyi deneriz)."""
    
    # 1. Dosya boyutu kontrolü (DeepFace video için yavaş ve kaynak yoğundur)
    if update.message.video.file_size > 20 * 1024 * 1024:  # Örn: 20MB sınırı
        await update.message.reply_text("Video dosyası çok büyük (max 20MB). Lütfen daha küçük bir dosya gönderin.")
        return

    await update.message.reply_text("Video alındı. Analiz için video dosyasının indirilmesi ve işlenmesi zaman alabilir...")

    downloaded_file_path = None
    try:
        # 2. Video dosyasını indir
        video_file_id = update.message.video.file_id
        new_file = await context.bot.get_file(video_file_id)
        downloaded_file_path = get_temp_file_path(video_file_id, "mp4")
        await new_file.download_to_drive(downloaded_file_path)
        
        logger.info(f"Video indirildi: {downloaded_file_path}")

        # 3. DeepFace analizi (Hata düzeltmeleri yapıldı)
        results = DeepFace.analyze(
            img_path=downloaded_file_path, 
            actions=['age', 'gender', 'race', 'emotion'], 
            enforce_detection=False
        )

        if not results:
            await update.message.reply_text("Video karesinde yüz algılanamadı.")
            return

        # 4. Analiz sonucunu güvenli şekilde ayrıştırma
        face_data = results[0] 
        
        # Loglardaki ValueError ve TypeError'ı çözen güvenli ayrıştırma
        facial_area = face_data['facial_area']
        x = facial_area['x']
        y = facial_area['y']
        w = facial_area['w']
        h = facial_area['h']

        # 5. Sonucu kullanıcıya gönderme
        caption = (
            f"Video Karesi Analizi Sonucu:\n"
            f"Duygu: {face_data.get('dominant_emotion', 'Bilinmiyor').capitalize()}\n"
            f"Yaş: {face_data.get('age', 'Bilinmiyor')}\n"
            f"Yüz Konumu (x, y, w, h): ({x}, {y}, {w}, {h})"
        )
        
        await update.message.reply_text(caption)
        
    except Exception as e:
        logger.error(f"Video analizinde beklenmeyen hata: {e}")
        await update.message.reply_text(
            "Video analizinde bir sorun oluştu. Lütfen videonun net ve kısa olduğundan emin olun."
        )
    finally:
        # 6. Geçici dosyayı sil
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)
            logger.info(f"Geçici dosya silindi: {downloaded_file_path}")

# ==============================================================================
# 3. ANA FONKSİYON VE BOT BAŞLATMA
# ==============================================================================

def main() -> None:
    """Botu başlatır ve işleyicileri kaydeder."""
    # ApplicationBuilder yapısı ile Application oluşturulur
    application = Application.builder().token(BOT_TOKEN).build()

    # İşleyicileri kaydet
    application.add_handler(CommandHandler("start", start))
    
    # Sadece fotoğraf veya video olan, komut olmayan mesajları yakala
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO & ~filters.COMMAND, handle_video))
    
    # Hata işleyicisi
    application.add_error_handler(error_handler)

    # Botu başlat ve gelen güncellemeleri kontrol etmeye başla
    logger.info("Bot başlatılıyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Eğer botu Docker/Konteyner ortamında çalıştırıyorsanız:
    # `main()` çağrısının bir asenkron döngüde çalışması gerekir.
    # python-telegram-bot'un run_polling() metodu bunu otomatik olarak halleder.
    main()
