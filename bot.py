from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

OWNER_USERNAME = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"  # sadece owner komutu çalıştırabilir

async def serverst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != OWNER_USERNAME:
        await update.message.reply_text("Bu komutu sadece owner kullanabilir.")
        return

    bot = context.bot

    try:
        chat_list = await bot.get_updates()
        group_names = set()

        for update_item in chat_list:
            chat = getattr(update_item.message, "chat", None)
            if chat and chat.type in ["group", "supergroup"]:
                group_names.add(chat.title)

        if not group_names:
            await update.message.reply_text("Bot şu anda hiçbir grupta değil.")
            return

        msg = "📋 Botun bulunduğu gruplar:\n\n" + "\n".join(f"- {name}" for name in group_names)
        sent_msg = await update.message.reply_text(msg)

        # İsteğe bağlı: belirli bir süre sonra mesajı sil
        try:
            await sent_msg.delete()
        except Exception as e:
            error_message = str(e)
            if "message can't be deleted" in error_message or "not an administrator" in error_message:
                print("Uyarı: Bot mesajı silemedi (yetki eksikliği).")
            else:
                raise  # farklı bir hata varsa program durmasın

    except Exception as e:
        await update.message.reply_text(f"Bir hata oluştu: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token("BURAYA_TOKENİNİ_YAZ").build()
    app.add_handler(CommandHandler("serverst", serverst))
    app.run_polling()    downloaded_file_path = None
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
