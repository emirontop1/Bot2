import telegram
# Filters artık ayrı bir modül olan 'telegram' altından 'filters' olarak gelir.
# Updater, CommandHandler, MessageHandler, telegram.ext içinden alınır.
from telegram.ext import Application, CommandHandler, MessageHandler 
from telegram import filters, ParseMode
import logging
import os

# Web Scraping için: pytube (YouTube video bilgilerini çeker)
from pytube import YouTube
from pytube.exceptions import VideoUnavailable, RegexMatchError

# Günlüklemeyi (logging) ayarlayın
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Telegram Bot Token'ınızı ortam değişkeninden alın.
# Botunuzun TOKEN'ı: 8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU')

# Sayıları okunabilir formatta biçimlendirme
def format_number(num):
    """Sayıları binlik ayraçla (örnek: 1.234.567) biçimlendirir."""
    try:
        # Türkiye/Avrupa formatına uygun olarak virgülleri noktayla değiştirme
        return f"{num:,}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return str(num)

# Asenkron (Async) olarak çalışan istatistik çekme fonksiyonu
async def get_youtube_stats_scraper(url):
    """pytube kullanarak video ve kanal istatistiklerini çeker (API gerektirmez)."""
    try:
        yt = YouTube(url)

        # Video istatistikleri
        video_title = yt.title
        channel_title = yt.author
        view_count_f = format_number(yt.views)
        
        # Beğeni sayısı: YouTube bunu gizlediği için 0 veya None dönebilir.
        like_count_f = "Gizli/Çekilemiyor" 
        try:
             # Eğer pytube beğeniyi çekebilirse (Not: Bu özellik güvensizdir)
            if yt.rating is not None:
                # pytube rating'i 1-5 arasında bir değer olarak dönebilir. 
                # Gerçek beğeni sayısını almak zor olduğu için boş bırakmak daha güvenlidir.
                like_count_f = "Scraping ile belirsiz" 
        except Exception:
            pass # Hata durumunda varsayılan değeri tut

        # Sonuç mesajını oluşturma
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
# v20+ sürümünde tüm işleyici fonksiyonları asenkron (async) olmalıdır.
async def start(update, context):
    """Bot başlatıldığında gönderilen mesaj."""
    await update.message.reply_text(
        'Merhaba! Bana bir YouTube video linki gönderin, size istatistiklerini göstereyim. '
        'Bu bot YouTube API kullanmaz, bu yüzden bazı detaylı istatistikler (abone sayısı) '
        'bulunamayabilir.',
        parse_mode=ParseMode.MARKDOWN
    )

# Gelen mesajları işleme (YouTube linki bekleniyor)
async def handle_message(update, context):
    """Gelen mesajı kontrol eder ve YouTube linki ise istatistikleri çeker."""
    text = update.message.text
    
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
        await update.message.reply_text('Lütfen geçerli bir YouTube video linki gönderin.')

# Ana fonksiyon
def main():
    """Botu başlatır."""
    if TELEGRAM_BOT_TOKEN == '8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU':
        logger.warning("TELEGRAM_BOT_TOKEN'ı ortam değişkeni olarak ayarlamanız önerilir.")
    
    # v20+ sürümünde Updater yerine Application kullanılır.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Komut işleyicileri
    application.add_handler(CommandHandler("start", start))

    # Mesaj işleyicisi (gelen tüm metinler için)
    # filters.TEXT ve filters.COMMAND kullanılır.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot Polling ile Başlatılıyor...")
    
    # Botu başlatma (Polling modu)
    application.run_polling()

if __name__ == '__main__':
    main()
