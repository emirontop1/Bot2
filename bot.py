import telegram
from telegram.ext import Application, CommandHandler, MessageHandler 
import logging
import os
import re 
import math # Matematik fonksiyonları için

# Günlüklemeyi ayarlayın
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU')

# --- Yardımcı Fonksiyonlar ---

def safe_evaluate_expression(expression):
    """
    Kullanıcı tarafından verilen ifadeyi güvenli bir şekilde değerlendirir
    ve sonucu adım adım açıklar.
    """
    # İfadede izin verilen karakterler: sayılar, +, -, *, /, (, ), ., ve math fonksiyonları
    # Bu, komut enjeksiyonunu önlemek için hayati öneme sahiptir.
    allowed_chars = r'[0-9\.\+\-\*/\(\)\s]|sqrt|pow|sin|cos|tan|log'
    if not re.fullmatch(allowed_chars, expression.replace(' ', '')):
        return "Geçersiz ifade.", "Lütfen sadece sayıları ve temel işlemleri (\\+, \\-, \\*, \\/) kullanın. Fonksiyonlar: sqrt(), pow(x, y)."

    # math kütüphanesindeki fonksiyonları kullanıma açan güvenli kapsam
    safe_globals = {"__builtins__": None}
    safe_locals = {"sqrt": math.sqrt, "pow": math.pow, "sin": math.sin, "cos": math.cos, "tan": math.tan, "log": math.log}
    
    # Kullanıcının verdiği ifadeyi Python'ın anlayacağı hale getiriyoruz
    # Karekök için `sqrt()` ve üs almak için `pow(x, y)` desteklenir.
    
    adimlar = []
    
    try:
        # Sonucu hesapla
        result = eval(expression, safe_globals, safe_locals)
        
        # Adımları oluşturma (Manuel Açıklama)
        adimlar.append(f"<b>1\\. Adım: İfadeyi Tanımlama</b>")
        adimlar.append(f"İstenen hesaplama: <code>{expression}</code>")

        if 'sqrt' in expression or 'pow' in expression:
             adimlar.append(f"<b>2\\. Adım: Fonksiyonları Hesaplama</b>")
             adimlar.append(f"Karekök (sqrt) veya Üs alma (pow) işlemleri, Python'ın <code>math</code> kütüphanesi ile gerçekleştirilir.")

        adimlar.append(f"<b>3\\. Adım: Sonuçlandırma</b>")
        adimlar.append(f"Tüm işlemler sırasıyla (çarpma, bölme, toplama, çıkarma) yapıldıktan sonra final sonuca ulaşılır\\.")
        
        # Sonucu formatlama
        final_result = f"<b>Final Sonuç:</b> {result}"
        
        return "\n".join(adimlar), final_result
        
    except (NameError, TypeError, SyntaxError, ZeroDivisionError) as e:
        return f"Hata", f"<b>İfade Hatası:</b> Lütfen ifadenizi kontrol edin. ({type(e).__name__}: {e})"
    except Exception as e:
        return f"Hata", f"Beklenmedik bir hata oluştu: {e}"

# --- Telegram İşleyicileri (Handlers) ---

async def start(update, context):
    """/start komutu işleyicisi."""
    message = (
        "Merhaba\\! Ben bir Hesap Makinesi Botuyum\\.\n"
        "Bana bir matematiksel ifade yazın, size sonucu adım adım açıklayayım\\.\n\n"
        "<b>Örnekler:</b>\n"
        "<code>(15 \\* 4) \\+ sqrt(81)</code>\n"
        "<code>pow(2, 5) \\- 10</code>"
    )
    await update.message.reply_text(message, parse_mode="HTML") 

async def handle_message(update, context):
    """Gelen tüm metin mesajlarını işler ve matematiksel olarak çözer."""
    text = update.message.text
    
    if text is None:
        return
        
    # Komut Kontrolü: Komutsa yoksay
    if text.startswith('/'):
        return 

    # Mesajı işlemek için bekleme mesajı gönder
    initial_message = await update.message.reply_text("İşlem değerlendiriliyor...", parse_mode="HTML")
    
    # İfadeyi değerlendir
    adimlar, sonuc = safe_evaluate_expression(text.strip())
    
    # Kullanıcıya tüm adımları ve sonucu gönder
    full_response = adimlar + "\n\n" + sonuc
    
    # Mesajı güncelle
    await initial_message.edit_text(full_response, 
                                    parse_mode="HTML") 

# --- Ana Fonksiyon ---

def main():
    """Botu başlatır."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    
    # Filtresiz MessageHandler: Tüm metin mesajlarını handle_message'a gönderir
    application.add_handler(MessageHandler(None, handle_message)) 

    logger.info("Bot Polling ile Başlatılıyor...")
    application.run_polling()

if __name__ == '__main__':
    main()
