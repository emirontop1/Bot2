import logging
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatType

# ==============================================================================
# 1. TEMEL AYARLAR
# ==============================================================================

# Lütfen BURAYI kendi Telegram Bot token'ınızla değiştirin!
BOT_TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU" 

# Loglama ayarları
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================================================================
# 2. İŞLEYİCİ FONKSİYONLAR
# ==============================================================================

# /start komutunu işler (Grup ayarı hatırlatması)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start komutunu işler ve kullanım talimatlarını verir."""
    
    if update.effective_chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        text = (
            "⚠️ **Uyarı: Ben bir Silme Botu'yum!**\n\n"
            "Beni bir gruba ekleyip yönetici yaparsanız, `delete_all` komutunu gönderene kadar "
            "bu gruptaki **yeni gelen TÜM mesajları silerim**.\n\n"
            "**Kullanım:**\n"
            "1. Beni yönetici yapın ve **mesaj silme yetkisi** verin.\n"
            "2. Silme işlemini başlatmak için: `/delete_all`\n"
            "3. Durdurmak için: `/stop_deleting`"
        )
    else:
        text = (
            "Merhaba! Ben bir grup mesaj silme botuyum. Beni bir gruba yönetici olarak ekleyin ve "
            "`/delete_all` komutuyla silme işlemini başlatın."
        )

    await update.message.reply_markdown_v2(text)

# Silme işlemini başlatan komut
async def start_deleting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Silme modunu etkinleştirir."""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("Bu komut sadece gruplarda kullanılabilir.")
        return

    # Botun silme modunda olduğunu kaydetmek için context.chat_data kullan
    context.chat_data['deleting_enabled'] = True
    logger.info(f"Grup {chat_id} için silme modu ETKİNLEŞTİRİLDİ.")
    
    await update.message.reply_text(
        "🗑️ **Silme modu etkinleştirildi!**\n"
        "Şu andan itibaren gruptaki tüm yeni mesajlar silinecektir.\n"
        "Durdurmak için: /stop_deleting"
    )

# Silme işlemini durduran komut
async def stop_deleting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Silme modunu devre dışı bırakır."""
    chat_id = update.effective_chat.id
    
    context.chat_data['deleting_enabled'] = False
    logger.info(f"Grup {chat_id} için silme modu DEVRE DIŞI BIRAKILDI.")
    
    await update.message.reply_text(
        "✅ **Silme modu devre dışı bırakıldı!**\n"
        "Gruptaki mesajlar artık silinmeyecektir.\n"
        "Yeniden başlatmak için: /delete_all"
    )


# Tüm mesajları silen asıl işleyici
async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gelen mesajı silmeye çalışır."""
    
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    
    # Silme modu etkin mi?
    if not context.chat_data.get('deleting_enabled', False):
        return # Etkin değilse bir şey yapma

    # Mesajı silmeye çalış
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Mesaj silindi: Chat={chat_id}, MsgID={message_id}")
    except Exception as e:
        # Mesajı silme yetkisi yoksa veya mesaj çok eskiyse hata verir
        error_message = str(e)
        logger.error(f"Mesaj silinirken hata oluştu: {error_message}")
        
        # Bot ilk kez mesaj silemediğinde kullanıcıyı bilgilendir
        if "message can't be deleted" in error_message or "not an administrator" in error_message:
            # Sadece bir kez uyarı göndermek için silme modunu kapatabiliriz.
            context.chat_data['deleting_enabled'] = False 
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ **HATA: Mesajları silemiyorum!**\n"
                     "Lütfen botun grupta **Yönetici** olduğundan ve **mesaj silme yetkisine** sahip olduğundan emin olun."
            )

# ==============================================================================
# 3. ANA FONKSİYON VE BOT BAŞLATMA
# ==============================================================================

def main() -> None:
    """Botu başlatır ve işleyicileri kaydeder."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Komut İşleyicileri
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("delete_all", start_deleting))
    application.add_handler(CommandHandler("stop_deleting", stop_deleting))
    
    # Mesaj İşleyicisi
    # filters.ALL ve filters.UpdateType.MESSAGE: Gelen tüm mesajları (komutlar dahil) yakala
    # update.edited_message'ı da silmek isterseniz MessageHandler'ı update_types=["message", "edited_message"] ile kullanabilirsiniz.
    application.add_handler(MessageHandler(filters.ALL, delete_message))

    # Botu başlat
    logger.info("Mesaj Silme Botu başlatılıyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
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
