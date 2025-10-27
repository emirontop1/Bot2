import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import os
import re

# Web Scraping için: pytube (YouTube video bilgilerini çeker)
from pytube import YouTube
from pytube.exceptions import VideoUnavailable

# Günlüklemeyi (logging) ayarlayın
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Telegram Bot Token'ınızı ortam değişkeninden alın. Railway'de bu daha güvenli.
TELEGRAM_BOT_TOKEN = '8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU'

# Sayıları okunabilir formatta biçimlendirme
def format_number(num):
    """Sayıları binlik ayraçla (örnek: 1.234.567) biçimlendirir."""
    try:
        return f"{num:,}".replace(',', '.')
    except (ValueError, TypeError):
        return str(num)

def get_youtube_stats_scraper(url):
    """pytube kullanarak video ve kanal istatistiklerini çeker (API gerektirmez)."""
    try:
        yt = YouTube(url)

        # Video istatistikleri
        video_title = yt.title
        channel_title = yt.author
        view_count_f = format_number(yt.views)
        
        # pytube'da abone ve toplu görüntüleme sayısı doğrudan yoktur, 
        # bu veriler genellikle API veya daha karmaşık scraping gerektirir.
        # Basit bir scraping ile alabileceğimiz verilerle sınırlı kalıyoruz.
        
        # Beğeni sayısı: YouTube bunu gizlediği için 0 veya None dönebilir.
        try:
             # Eğer pytube beğeniyi çekebilirse
            like_count_f = format_number(yt.rating) 
        except Exception:
            # Çoğu zaman like sayısı scraping ile çekilemez veya anlamsız bir değer gelir.
            like_count_f = "Gizli/Çekilemiyor" 


        # Sonuç mesajını oluşturma
        message = (
            f"🎬 **Video İstatistikleri (API'siz)**\n"
            f"🔗 [**{video_title}**]({url})\n\n"
            f"👤 **Kanal Adı:** {channel_title}\n"
            f"👀 **Görüntüleme:** {view_count_f}\n"
            f"👍 **Beğeni:** {like_count_f}\n"
            f"⭐ **Abone Sayısı:** Bilinmiyor (API gerektirir)"
        )

        return message

    except VideoUnavailable:
        return "Video artık mevcut değil veya erişilebilir durumda değil."
    except Exception as e:
        logger.error(f"Scraping hatası: {e}")
        return "İstatistikler çekilirken bir hata oluştu. Linkin doğru olduğundan emin olun."

# /start komutu
def start(update, context):
    update.message.reply_text(
        'Merhaba! Bana bir YouTube video linki gönderin, size istatistiklerini göstereyim. '
        'Bu bot YouTube API kullanmaz, bu yüzden bazı detaylı istatistikler (abone sayısı) '
        'bulunamayabilir.',
        parse_mode=telegram.ParseMode.MARKDOWN
    )

# Gelen mesajları işleme (YouTube linki bekleniyor)
def handle_message(update, context):
    text = update.message.text
    
    # Basit URL kontrolü
    if 'youtube.com' in text or 'youtu.be' in text:
        update.message.reply_text("İstatistikler çekiliyor...")
        stats_message = get_youtube_stats_scraper(text)
        update.message.reply_text(stats_message, 
                                  parse_mode=telegram.ParseMode.MARKDOWN,
                                  disable_web_page_preview=True) 
    else:
        update.message.reply_text('Lütfen geçerli bir YouTube video linki gönderin.')

# Ana fonksiyon (Polling ile çalıştırmak üzere)
def main():
    """Botu başlatır."""
    if TELEGRAM_BOT_TOKEN == '8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU':
        logger.warning("TELEGRAM_BOT_TOKEN'ı ortam değişkeni olarak ayarlamanız önerilir.")
        
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    # Komut işleyicileri
    dp.add_handler(CommandHandler("start", start))

    # Mesaj işleyicisi (gelen tüm metinler için)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Railway'de Polling (uzun yoklama) ile çalıştırma. 
    # Not: Railway'in ücretsiz katmanında Polling botların sürekli çalışması garanti edilmez.
    # Sürekli çalışma garantisi için Webhook kurulumu önerilir.
    logger.info("Bot Polling ile Başlatılıyor...")
    updater.start_polling() 
    updater.idle()

if __name__ == '__main__':
    main()
