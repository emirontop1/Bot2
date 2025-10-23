from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

OWNER_USERNAME = "DincEMR"  # sadece owner kullanabilecek

# /serverst komutu
async def serverst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != OWNER_USERNAME:
        await update.message.reply_text("Bu komutu sadece owner kullanabilir.")
        return

    bot = context.bot
    chat_list = await bot.get_updates()
    group_names = set()

    # Güncellemelerden botun bulunduğu grupları toplar
    for update_item in chat_list:
        chat = getattr(update_item.message, "chat", None)
        if chat and chat.type in ["group", "supergroup"]:
            group_names.add(chat.title)

    if not group_names:
        await update.message.reply_text("Bot şu anda hiçbir grupta değil.")
        return

    msg = "📋 Botun bulunduğu gruplar:\n\n" + "\n".join(f"- {name}" for name in group_names)
    await update.message.reply_text(msg)

# Botu başlat
if __name__ == "__main__":
    app = ApplicationBuilder().token("BURAYA_TOKENİNİ_YAZ").build()
    app.add_handler(CommandHandler("serverst", serverst))
    app.run_polling()        
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
