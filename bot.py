import telegram
# Filters artık kullanılmıyor
from telegram.ext import Application, CommandHandler, MessageHandler 
from telegram import ParseMode
import logging
import os
import re # Komut kontrolü için re eklendi

# Web Scraping için: pytube
from pytube import YouTube
from pytube.exceptions import VideoUnavailable, RegexMatchError

# Günlüklemeyi (logging) ayarlayın
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Telegram Bot Token'ınız ortam değişkeninden alın.
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU')

# Sayıları okunabilir formatta biçimlendirme
def format_number(num):
    """Sayıları binlik ayraçla (örnek: 1.234.567) biçimlendirir."""
    try:
        return f"{num:,}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return str(num)

# Asenkron (Async) olarak çalışan istatistik çekme fonksiyonu
async def get_youtube_stats_scraper(url):
    """pytube kullanarak video ve kanal istatistiklerini çeker (API gerektirmez)."""
    # ... (pytube ile istatistik çekme mantığı aynı kalır)
    try:
        yt = YouTube(url)

        video_title = yt.title
        channel_title = yt.author
        view_count_f = format_number(yt.views)
        
        like_count_f = "Gizli/Çekilemiyor" 
        try:
            if yt.rating is not None:
                like_count_f = "Scraping ile belirsiz" 
        except Exception:
            pass 

        message = (
            f"🎬 **Video İstatistikleri (API'siz)**\n"
            f"🔗 [**{video_title}**]({url})\n\n"
            f"👤 **Kanal Adı:** {channel_title}\n"
            f"👀 **Görüntüleme:** {view_count_f}\n"
            f"👍 **Beğeni:** {like_count_f}\n"
            f"⭐ **Abone Sayısı:** Bilinmiyor (API/Detaylı Scraping gerektirir)"
        )

        return message

    except VideoUnavailable:
        return "Video artık mevcut değil veya erişilebilir durumda değil."
    except RegexMatchError:
        return "Gönderilen link geçerli bir YouTube video URL'si gibi görünmüyor."
    except Exception as e:
        logger.error(f"Scraping hatası: {e}")
        return "İstatistikler çekilirken beklenmedik bir hata oluştu."

# /start komutu işleyicisi
async def start(update, context):
    """Bot başlatıldığında gönderilen mesaj."""
    await update.message.reply_text(
        'Merhaba! Bana bir YouTube video linki gönderin, size istatistiklerini göstereyim. '
        'Bu bot API kullanmaz.',
        parse_mode=ParseMode.MARKDOWN
    )

# Gelen mesajları işleme (YouTube linki bekleniyor)
async def handle_message(update, context):
    """Gelen mesajı kontrol eder ve YouTube linki ise istatistikleri çeker."""
    text = update.message.text
    
    if text is None:
        # Metin mesajı değilse (örneğin resim, sticker) işlem yapma
        return
        
    # **KOMUT KONTROLÜ (FİLTRE YERİNE BU KULLANILDI)**
    if text.startswith('/'):
        # Mesaj bir komutla başlıyorsa (örneğin /help), yoksay.
        return 
    # **KOMUT KONTROLÜ SONU**

    # Basit URL kontrolü
    if 'youtube.com' in text or 'youtu.be' in text:
        # Önce kullanıcıya bekleme mesajı gönder
        initial_message = await update.message.reply_text("İstatistikler çekiliyor...")
        
        # İstatistikleri çek ve mesajı düzenle
        stats_message = await get_youtube_stats_scraper(text)
        
        # Gönderilen ilk mesajı istatistiklerle güncelle
        await initial_message.edit_text(stats_message, 
                                        parse_mode=ParseMode.MARKDOWN,
                                        disable_web_page_preview=True) 
    else:
        # Komut değil, link de değilse kullanıcıya geri bildirim ver
        await update.message.reply_text('Lütfen geçerli bir YouTube video linki gönderin.')

# Ana fonksiyon
def main():
    """Botu başlatır."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Komut işleyicileri
    application.add_handler(CommandHandler("start", start))

    # Mesaj işleyicisi (Gelen *tüm* metin mesajlarına tepki verir)
    # Filtre kullanmadığımız için filters.TEXT kullanmaya da gerek yok.
    application.add_handler(MessageHandler(None, handle_message)) 

    logger.info("Bot Polling ile Başlatılıyor...")
    
    # Botu başlatma (Polling modu)
    application.run_polling()

if __name__ == '__main__':
    main()
