import telegram
from telegram.ext import Application, CommandHandler, MessageHandler 
import logging
import os
import re 

# Scraping için yeni kütüphaneler
import requests
from bs4 import BeautifulSoup
import json # Sayfadaki JSON verisini çekmek için

# ... (Diğer importlar ve logging aynı kalır)

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU')

# ... (format_number ve escape_html fonksiyonları aynı kalır)
def format_number(num):
    """Sayıları okunabilir formatta biçimlendirir."""
    try:
        return f"{num:,}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return str(num)

def escape_html(text):
    """HTML formatı için gerekli temel karakterleri kaçırır."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    

# --- Ana İşlevsellik: YENİ SCRAPER ---

async def get_youtube_stats_scraper(url):
    """requests ve BeautifulSoup kullanarak istatistikleri çeker."""
    
    # YouTube, botları engellediği için, web tarayıcısı gibi görünmek önemlidir.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 1. Sayfa içeriğini çekme
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # HTTP hatası varsa istisna fırlat

        # 2. Görüntüleme sayısı ve başlığı HTML'den alma
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Youtube verilerinin tutulduğu ana JSON bloğunu arama
        data = None
        for script in soup.find_all('script'):
            if 'ytInitialPlayerResponse' in script.text:
                # JSON verisi bir JavaScript değişkeni içinde gömülü
                json_str = script.text.split('var ytInitialPlayerResponse = ')[-1].split(';var meta = document')[0]
                data = json.loads(json_str)
                break

        if not data:
            return "Veri çekilirken kritik hata: Sayfa yapısı değişmiş olabilir."

        # İstatistikleri JSON bloğundan çekme
        video_details = data.get('videoDetails', {})
        
        video_title = escape_html(video_details.get('title', 'Başlık Bulunamadı'))
        channel_title = escape_html(video_details.get('author', 'Kanal Bulunamadı'))
        
        view_count = video_details.get('viewCount', 0)
        view_count_f = format_number(int(view_count)) if view_count else "Bilinmiyor"
        
        # Beğenileri çekmek bu yöntemle çok zor olduğu için sabit bırakılır
        like_count_f = "Gizli/Çekilemiyor"

        # HTML formatında mesaj
        message = (
            f"🎬 <b>Video İstatistikleri (Scraping)</b>\n"
            f'🔗 <a href="{url}">{video_title}</a>\n\n'
            f"👤 <b>Kanal Adı:</b> {channel_title}\n"
            f"👀 <b>Görüntüleme:</b> {view_count_f}\n"
            f"👍 <b>Beğeni:</b> {like_count_f}\n"
            f"⭐ <b>Abone Sayısı:</b> Bilinmiyor (Scraping kısıtlaması)"
        )

        return message

    except requests.exceptions.HTTPError as e:
        return f"HTTP Hatası: {e.response.status_code}. Erişim engellenmiş olabilir."
    except requests.exceptions.RequestException:
        return "Bağlantı hatası veya zaman aşımı."
    except Exception as e:
        logger.error(f"Genel Scraping Hatası: {e}")
        return "İstatistikler çekilirken beklenmedik bir hata oluştu. (Genel Hata)"

# --- Telegram İşleyicileri (Handlers) ---

# ... (start ve handle_message fonksiyonları ile main fonksiyonu aynı kalır, 
# çünkü onlar artık doğru çalışıyor ve sadece parse_mode="HTML" kullanıyor.)

async def start(update, context):
    """/start komutu işleyicisi."""
    await update.message.reply_text(
        'Merhaba! Bana bir YouTube video linki gönderin, size istatistiklerini göstereyim.',
        parse_mode="HTML" 
    )

async def handle_message(update, context):
    """Gelen tüm mesajları işler."""
    text = update.message.text
    
    if text is None:
        return
        
    if text.startswith('/'):
        return 

    if 'youtube.com' in text or 'youtu.be' in text:
        initial_message = await update.message.reply_text("İstatistikler çekiliyor...", parse_mode="HTML")
        
        stats_message = await get_youtube_stats_scraper(text)
        
        await initial_message.edit_text(stats_message, 
                                        parse_mode="HTML",
                                        disable_web_page_preview=True) 
    else:
        await update.message.reply_text('Lütfen geçerli bir YouTube video linki gönderin.', parse_mode="HTML")

def main():
    """Botu başlatır."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(None, handle_message)) 

    logger.info("Bot Polling ile Başlatılıyor...")
    application.run_polling()

if __name__ == '__main__':
    main()
