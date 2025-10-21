import os
import logging
import random
import string
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ==============================================================================
# LUA PARSER VE GİZLEME (OBFUSCATION) İŞLEVLERİ
# luamin yerine luaparser kullanılarak istenen mantık uygulanır.
# ==============================================================================

try:
    from luaparser import ast
    from luaparser.ast import Name, LocalAssign, LocalFunction, Chunk, Block
    from luaparser.ast.visitor import ASTRecursiveVisitor
    from luaparser.codegen import to_lua
except ImportError:
    # Eğer luaparser kurulu değilse veya import edilemezse
    print("HATA: 'luaparser' kütüphanesi bulunamadı. Lütfen 'pip install luaparser' komutunu çalıştırın.")
    exit(1)

# Ayarlar
TOKEN = "8350124542:AAHwsh0LksJAZOW-hHTY1BTu5i8-XKGFn18"

# Logging ayarları
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def generate_random_name(length=8):
    """Rastgele okunaksız değişken adı üretir."""
    # Başlangıç karakteri harf olmalı (Lua gereksinimi)
    chars = string.ascii_letters + string.digits
    return random.choice(string.ascii_letters) + ''.join(random.choice(chars) for _ in range(length - 1))

def obfuscate_lua_code(lua_code: str) -> str:
    """
    Lua kodunu gizler:
    1. Yerel değişken adlarını değiştirir (randomize).
    2. Tüm yerel atamaları (LocalAssign) dosyanın en üstüne taşır.
    """
    try:
        # Kodu Çözümleme (Parse)
        tree = ast.parse(lua_code)
    except Exception as e:
        logger.error(f"Lua kodunu çözerken hata oluştu: {e}")
        return "HATA: Geçersiz Lua Kodu. Çözümleme başarısız."

    name_map = {}
    local_assignments = []
    
    # AST üzerinde gezinen ve yerel değişkenleri toplayan/değiştiren ziyaretçi
    class ObfuscatorVisitor(ASTRecursiveVisitor):
        
        def visit_LocalAssign(self, node):
            # Yerel atamaları listeye ekle (daha sonra başa taşınacak)
            local_assignments.append(node)
            
            # Atama hedeflerini (targets) gizle
            for target in node.targets:
                if isinstance(target, Name):
                    old_name = target.id
                    if old_name not in name_map:
                        name_map[old_name] = generate_random_name()
                    
                    # AST'deki ismi yeni isimle değiştir
                    target.id = name_map[old_name]

            # Atamanın sağ tarafındaki değerleri ziyaret etmeye devam et
            super().visit_LocalAssign(node)
        
        def visit_Name(self, node):
            # Normal isimleri (kullanımları) haritada varsa değiştir
            if node.id in name_map:
                node.id = name_map[node.id]
            super().visit_Name(node)
            
        def visit_LocalFunction(self, node):
            # Yerel fonksiyon isimlerini değiştir
            old_name = node.name.id
            if old_name not in name_map:
                name_map[old_name] = generate_random_name()
            node.name.id = name_map[old_name]
            
            # Fonksiyon gövdesini ziyaret etmeye devam et
            super().visit_LocalFunction(node)

    # Gizleme işlemini başlat
    visitor = ObfuscatorVisitor()
    visitor.visit(tree)

    # 1. Yerel atamaları ana gövdeden çıkar
    new_body = []
    # Yerel atamaların bir kopyasını alıp orijinal gövdeden çıkarıyoruz
    local_assignment_nodes = set(local_assignments)

    # Ana gövde düğümlerini filtrele
    for node in tree.body.body:
        if node not in local_assignment_nodes:
            new_body.append(node)
            
    # 2. Gizlenmiş yerel atamaları en üste taşı
    final_body = local_assignments + new_body
    
    # 3. Yeni AST'yi oluştur
    new_tree = Chunk(Block(final_body))

    # 4. AST'yi tekrar koda dönüştür
    obfuscated_code = to_lua(new_tree)
    
    # luaparser, 'local' kelimesini atamaları taşırken silmiş olabilir, 
    # ancak ObfuscatorVisitor'da LocalAssign düğümünü koruduğumuz için 
    # to_lua'nın bunu doğru üretmesi beklenir.

    return obfuscated_code

# ==============================================================================
# TELEGRAM BOT İŞLEVLERİ
# ==============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot başladığında /start komutunu işler."""
    await update.message.reply_text(
        "Merhaba! Ben Lua Kod Gizleme Botuyum. Bana gizlemek istediğiniz Lua kodunu `/obfuscate [KOD]` formatında gönderin."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help komutunu işler."""
    await update.message.reply_text(
        "Kullanım:\n\n"
        "`/obfuscate [Lua Kodu]` - Girdiğiniz Lua kodunu gizler (değişken adlarını değiştirir, local atamaları başa taşır).\n"
        "`/start` - Bot hakkında bilgi.\n"
        "`/help` - Bu yardım mesajı."
    )

async def obfuscate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/obfuscate komutunu işler ve gizleme işlevini kullanır."""
    if not context.args:
        await update.message.reply_text(
            "Lütfen gizlemek istediğiniz Lua kodunu komutun arkasına yazın.\nÖrnek: `/obfuscate local x = 1; print(x)`"
        )
        return

    # Tüm argümanları birleştirerek Lua kodunu al
    lua_code_to_obfuscate = " ".join(context.args)

    logger.info(f"Gizlenecek kod alındı: {lua_code_to_obfuscate[:50]}...")
    
    # Gizleme işlemini gerçekleştir
    obfuscated_code = obfuscate_lua_code(lua_code_to_obfuscate)

    if obfuscated_code.startswith("HATA:"):
        await update.message.reply_text(f"Gizleme başarısız: {obfuscated_code}")
    else:
        # Kodun okunabilirliğini artırmak için Markdown ile gönder
        await update.message.reply_text(
            f"**Gizlenmiş Lua Kodu:**\n```lua\n{obfuscated_code}\n```",
            parse_mode='Markdown'
        )

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bilinen komutlar dışındaki mesajları yanıtlar."""
    await update.message.reply_text(f"Üzgünüm, '{update.message.text}' komutunu anlamadım.")


def main() -> None:
    """Botu başlatır ve Telegram işleyicilerini (handlers) ayarlar."""
    # Application oluşturma
    application = Application.builder().token(TOKEN).build()

    # Komut işleyicilerini (handlers) ekleme
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("obfuscate", obfuscate_command))
    
    # Bilinmeyen komutlar için işleyici (tüm mesajları filtreler, komut olmayanları)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Botu çalıştırma
    logger.info("Bot başlatılıyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

