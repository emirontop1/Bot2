import telegram
from telegram.ext import Application, CommandHandler, MessageHandler 
import logging
import os
import re 

# Web Scraping için: pytube (Bağımlılıklarda olduğundan emin olun)
from pytube import YouTube
from pytube.exceptions import VideoUnavailable, RegexMatchError

# Günlüklemeyi ayarlayın
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU')

# --- Yardımcı Fonksiyonlar ---

def format_number(num):
    """Sayıları okunabilir formatta biçimlendirir."""
    try:
        return f"{num:,}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return str(num)

def escape_html(text):
    """HTML formatı için gerekli temel karakterleri kaçırır."""
    # HTML için sadece &, <, > karakterleri kaçırılmalıdır.
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
# --- Ana İşlevsellik ---

async def get_youtube_stats_scraper(url):
    """pytube kullanarak istatistikleri çeker."""
    try:
        yt = YouTube(url)

        # HTML formatı için kaçırılmış başlık ve kanal adı
        video_title = escape_html(yt.title)
        channel_title = escape_html(yt.author)
        view_count_f = format_number(yt.views)
        
        like_count_f = "Gizli/Çekilemiyor" 
        
        # HTML formatında mesaj (<b> bold, <i> italic, <a> link)
        message = (
            f"🎬 <b>Video İstatistikleri (API'siz)</b>\n"
            f'🔗 <a href="{url}">{video_title}</a>\n\n'
            f"👤 <b>Kanal Adı:</b> {channel_title}\n"
            f"👀 <b>Görüntüleme:</b> {view_count_f}\n"
            f"👍 <b>Beğeni:</b> {like_count_f}\n"
            f"⭐ <b>Abone Sayısı:</b> Bilinmiyor (Scraping kısıtlaması)"
        )

        return message

    except VideoUnavailable:
        return "Video artık mevcut değil veya erişilebilir durumda değil."
    except RegexMatchError:
        return "Gönderilen link geçerli bir YouTube video URL'si gibi görünmüyor."
    except Exception as e:
        logger.error(f"Scraping hatası: {e}")
        return "İstatistikler çekilirken beklenmedik bir hata oluştu."


# --- Telegram İşleyicileri (Handlers) ---

async def start(update, context):
    """/start komutu işleyicisi."""
    await update.message.reply_text(
        'Merhaba! Bana bir YouTube video linki gönderin, size istatistiklerini göstereyim.',
        parse_mode="HTML" # HTML parse modu kullanılıyor
    )

async def handle_message(update, context):
    """Gelen tüm mesajları işler."""
    text = update.message.text
    
    if text is None:
        return
        
    # KOMUT KONTROLÜ
    if text.startswith('/'):
        return 

    # Basit URL kontrolü
    if 'youtube.com' in text or 'youtu.be' in text:
        initial_message = await update.message.reply_text("İstatistikler çekiliyor...", parse_mode="HTML")
        
        stats_message = await get_youtube_stats_scraper(text)
        
        # Mesajı güncelle ve HTML kullan
        await initial_message.edit_text(stats_message, 
                                        parse_mode="HTML",
                                        disable_web_page_preview=True) 
    else:
        await update.message.reply_text('Lütfen geçerli bir YouTube video linki gönderin.', parse_mode="HTML")

# --- Ana Fonksiyon ---

def main():
    """Botu başlatır."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    
    # Filtresiz MessageHandler
    application.add_handler(MessageHandler(None, handle_message)) 

    logger.info("Bot Polling ile Başlatılıyor...")
    application.run_polling()

if __name__ == '__main__':
    main()
