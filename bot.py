import logging
import io
from telegram import Update, File, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import luamin # Lua kodunu minify/obfuscate etmek için bu kütüphaneyi kullanacağız

# --- DİKKAT: GÜVENLİK RİSKİ! ---
# Token'ı buraya yapıştıracaksınız.
# Bu kodun olduğu GitHub reposu KESİNLİKLE "Private" (Gizli) olmalıdır.
# Aksi halde botunuz saniyeler içinde çalınır.
TOKEN = "8350124542:AAHwsh0LksJAZOW-hHTY1BTu5i8-XKGFn18"

# Logging (Hata takibi) ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start komutu verildiğinde çalışır."""
    await update.message.reply_text(
        'Merhaba! Ben bir Lua Obfuscator Botuyum.\n'
        'Bana bir .lua dosyası gönderin veya Lua kodunuzu metin olarak yapıştırın.\n'
        'Kodunuzu `luamin` ile küçültüp (minify) size geri göndereceğim.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help komutu verildiğinde çalışır."""
    await update.message.reply_text(
        'Bana bir .lua dosyası veya düz metin olarak Lua kodu gönderin. '
        'Kod, okunması zor olacak şekilde küçültülecektir (minified). '
        'Bu, değişken adlarını şifrelemez ancak boşlukları ve yorumları kaldırır.'
    )

def obfuscate_lua_code(code_string: str) -> str:
    """
    Verilen Lua kodunu luamin kullanarak minify eder (küçültür).
    Bu, tam bir şifreleme değil, kod küçültme ve basitleştirilmiş bir obfuscation işlemidir.
    """
    try:
        # luamin.minify fonksiyonunu çağır
        obfuscated_code = luamin.minify(code_string)
        return obfuscated_code
    except Exception as e:
        logger.error(f"luamin hatası: {e}")
        # Hata olursa, kullanıcıya hatayı bildir
        return f"-- HATA: Kodunuz işlenemedi.\n-- Python Hatası: {e}\n\n-- Orijinal Kod:\n{code_string}"

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Metin olarak gönderilen kodları işler."""
    user_code = update.message.text
    logger.info("Metin olarak Lua kodu alındı.")
    
    await update.message.reply_text("Kodunuz işleniyor, lütfen bekleyin...")

    # Kodu obfuscate et
    obfuscated_code = obfuscate_lua_code(user_code)

    # Obfuscate edilmiş kodu bir dosya olarak gönder
    # Telegram'ın 4096 karakter sınırına takılmamak için dosya olarak göndermek en iyisidir.
    try:
        output_file = io.BytesIO(obfuscated_code.encode('utf-8'))
        output_file.name = 'obfuscated.lua'
        
        await update.message.reply_document(
            document=output_file,
            filename='obfuscated.lua',
            caption='Lua kodunuz `luamin` ile küçültüldü.'
        )
    except Exception as e:
        logger.error(f"Dosya gönderme hatası: {e}")
        await update.message.reply_text(f"Kod işlendi ancak dosya gönderilirken bir hata oluştu: {e}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dosya olarak gönderilen kodları işler."""
    document = update.message.document
    
    # Sadece .lua dosyalarını kabul et
    if not document.file_name or not document.file_name.lower().endswith('.lua'):
        await update.message.reply_text("Lütfen sadece `.lua` uzantılı bir dosya gönderin.")
        return

    logger.info(f"Dosya alındı: {document.file_name}")
    await update.message.reply_text("Dosyanız indiriliyor ve işleniyor...")

    try:
        # Dosyayı indir
        file: File = await document.get_file()
        
        # Dosyayı hafızaya indir (diske yazmaya gerek yok)
        downloaded_file = io.BytesIO()
        await file.download_to_memory(downloaded_file)
        downloaded_file.seek(0) # Dosyanın başına dön
        
        # İçeriği oku
        user_code = downloaded_file.read().decode('utf-8')
        
        # Kodu obfuscate et
        obfuscated_code = obfuscate_lua_code(user_code)
        
        # Obfuscate edilmiş kodu yeni bir dosya olarak hazırla
        output_file = io.BytesIO(obfuscated_code.encode('utf-8'))
        output_file.name = f'obfuscated_{document.file_name}'

        # Yeni dosyayı kullanıcıya gönder
        await update.message.reply_document(
            document=output_file,
            filename=f'obfuscated_{document.file_name}',
            caption='Lua dosyanız `luamin` ile küçültüldü.'
        )

    except Exception as e:
        logger.error(f"Dosya işleme hatası: {e}")
        await update.message.reply_text(f"Dosyanızı işlerken bir hata oluştu: {e}")

def main() -> None:
    """Botu başlatır."""
    
    # Token'ın değiştirilip değiştirilmediğini kontrol et
    if TOKEN == "BURAYA_BOTFATHER_DAN_ALDIGINIZ_TOKENI_YAPISTIRIN":
        logger.critical("HATA: TOKEN ayarlanmamış!")
        logger.critical("Lütfen bot.py dosyasındaki TOKEN değişkenini kendi bot token'ınızla değiştirin.")
        return

    # Application'ı kur
    application = Application.builder().token(TOKEN).build()

    # Komutları ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Mesaj işleyicileri ekle
    # Önce .lua dosyalarını yakala
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    # Sonra normal metinleri (ama komutları değil) yakala
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Botu başlat
    logger.info("Bot başlatılıyor...")
    application.run_polling()

if __name__ == '__main__':
    main()
