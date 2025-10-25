import logging
import os
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Gelişmiş loglamayı etkinleştir (Hata ayıklama için yararlı)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token'ını ortam değişkeninden al (Railway için gereklidir)
# Railway'de "Variables" kısmına TELEGRAM_TOKEN olarak eklemelisiniz.
TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN ortam değişkeni ayarlanmamış!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start komutu verildiğinde bir karşılama mesajı gönderir."""
    await update.message.reply_html(
        "Merhaba! 👋\n\n"
        "Bana bir fotoğraf gönderin, onu anında tek bir HTML dosyasına dönüştüreyim. "
        "Oluşturulan HTML dosyası, görseli Base64 formatında içinde barındırır."
    )

def create_html_content(image_bytes: bytes, mime_type: str) -> str:
    """Görsel byte'larını Base64'e çevirir ve tam bir HTML sayfası oluşturur."""
    
    # Görseli Base64 string formatına çevir
    base64_string = base64.b64encode(image_bytes).decode('utf-8')
    
    # Veri URI'sini oluştur
    data_uri = f"data:{mime_type};base64,{base64_string}"
    
    # Tamamen kendi içinde yeterli (self-contained) bir HTML dosyası oluştur
    html_content = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Görsel HTML'e Gömüldü</title>
    <style>
        /* Sayfa kenar boşluklarını sıfırla */
        body, html {{
            margin: 0;
            padding: 0;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #2e2e2e; /* Arka plan rengi */
        }}
        
        /* Görselin maksimum genişlikte ve yükseklikte olmasını sağla */
        img {{
            max-width: 100%;
            max-height: 100vh; /* Ekran yüksekliğini geçmesin */
            height: auto;
            display: block;
            border-radius: 8px; /* Hafif köşelik */
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3); /* Göze hoş gelen gölge */
        }}
    </style>
</head>
<body>
    <!-- Görseli Base64 URI olarak buraya göm -->
    <img src="{data_uri}" alt="Yüklenen Görsel">
</body>
</html>
"""
    return html_content

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı bir fotoğraf gönderdiğinde çalışır."""
    message = update.message
    
    # Kullanıcıya işlem yapıldığını bildiren bir mesaj gönder
    processing_message = await message.reply_text("Görsel işleniyor, lütfen bekleyin...")

    try:
        # Telegram'da fotoğraflar farklı çözünürlüklerde gelir.
        # En yüksek çözünürlüklü olanı (-1) seçiyoruz.
        photo_file = await message.photo[-1].get_file()
        
        # Fotoğrafı byte olarak indiriyoruz
        file_bytes_io = await photo_file.download_as_bytearray()
        image_bytes = bytes(file_bytes_io)
        
        # Telegram'dan "photo" olarak gelen görseller genellikle JPEG formatındadır.
        # Eğer "document" olarak gelseydi mime_type'ı kontrol etmek gerekirdi.
        mime_type = "image/jpeg"
        
        # HTML içeriğini oluştur
        html_string = create_html_content(image_bytes, mime_type)
        
        # HTML içeriğini byte'a dönüştür
        html_bytes = html_string.encode('utf-8')
        
        # "İşleniyor" mesajını sil
        await context.bot.delete_message(chat_id=message.chat_id, message_id=processing_message.message_id)

        # Oluşturulan HTML'i bir dosya olarak gönder
        await message.reply_document(
            document=html_bytes,
            filename="gorsel.html",
            caption="İşte görseliniz HTML dosyasına gömüldü!"
        )

    except Exception as e:
        logger.error(f"Hata oluştu: {e}", exc_info=True)
        # "İşleniyor" mesajını sil (eğer hala varsa)
        try:
            await context.bot.delete_message(chat_id=message.chat_id, message_id=processing_message.message_id)
        except:
            pass # Mesaj zaten silinmişse veya başka bir hata olursa
            
        await message.reply_text("Maalesef bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

def main() -> None:
    """Botu başlatır."""
    
    # Application nesnesini oluştur
    application = Application.builder().token(TOKEN).build()

    # Komutları ekle
    application.add_handler(CommandHandler("start", start))

    # Fotoğraf mesajlarını işleyecek handler'ı ekle
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Botu polling (sürekli sorgulama) moduyla başlat
    # Railway'de bu 'worker' olarak çalışacaktır.
    logger.info("Bot başlatılıyor...")
    application.run_polling()

if __name__ == "__main__":
    main()
