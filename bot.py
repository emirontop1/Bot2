import logging
import os
from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

# --- AYARLAR ---
# Token'ı kodun içinden değil, Railway ortam değişkenlerinden al
TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"
if not TOKEN:
    raise ValueError("Lütfen 'TOKEN' adında bir ortam değişkeni ayarlayın!")
# -----------------

# Hata ayıklama için loglamayı etkinleştir
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komutunu yanıtlar."""
    await update.message.reply_text(
        "Merhaba! Render edilmesini istediğiniz bir .html veya .htm dosyasını bana gönderin. "
        "Dosyanın ekran görüntüsünü size göndereceğim."
    )

async def setup_selenium_driver():
    """Railway ortamı için optimize edilmiş Selenium WebDriver'ı kurar."""
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox") # Konteynerde root olarak çalışmak için GEREKLİ
    options.add_argument("--disable-dev-shm-usage") # Paylaşılan bellek sorunlarını önler
    options.add_argument("--disable-gpu") # GPU'ya gerek yok
    options.add_argument("--window-size=1280,1024") # Ekran boyutu
    
    # Dockerfile'da kurulan chromedriver'ı kullan
    # Genellikle /usr/bin/chromedriver konumunda olur ve PATH'e eklenir
    service = ChromeService() 
    
    return webdriver.Chrome(service=service, options=options)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gönderilen dökümanları işler."""
    document = update.message.document
    
    # 1. Dosya uzantısını kontrol et
    if not document.file_name or not document.file_name.lower().endswith(('.html', '.htm')):
        await update.message.reply_text("Lütfen bir .html veya .htm dosyası gönderin.")
        return

    await update.message.reply_text("HTML dosyası alındı. İşleniyor, lütfen bekleyin...")
    
    temp_html_path = None
    screenshot_path = None
    driver = None
    
    try:
        # 2. Dosyayı indir
        file = await context.bot.get_file(document.file_id)
        temp_html_path = f"temp_{document.file_id}.html"
        await file.download_to_drive(temp_html_path)
        
        # 3. Selenium'u ayarla
        driver = await setup_selenium_driver()
        
        # 4. Yerel HTML dosyasını aç
        full_file_path = "file://" + os.path.abspath(temp_html_path)
        driver.get(full_file_path)
        
        # 5. Ekran görüntüsü al
        screenshot_path = f"screenshot_{document.file_id}.png"
        driver.save_screenshot(screenshot_path)
        
        # Tarayıcıyı kapat
        driver.quit()
        
        # 6. Ekran görüntüsünü kullanıcıya gönder
        with open(screenshot_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo,
                caption=f"'{document.file_name}' dosyasının render edilmiş hali."
            )
            
    except Exception as e:
        logger.error(f"Hata oluştu: {e}", exc_info=True)
        await update.message.reply_text(f"Üzgünüm, dosyayı işlerken bir hata oluştu: {e}")
        
    finally:
        # 7. Geçici dosyaları temizle
        if driver:
            driver.quit()
        if temp_html_path and os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        if screenshot_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)

def main():
    """Botu başlatır."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Bot çalışıyor...")
    application.run_polling()

if __name__ == "__main__":
    main()
