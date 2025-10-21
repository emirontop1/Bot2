// bot.js

const TelegramBot = require('node-telegram-bot-api');
const luamin = require('luamin');
const { Buffer } = require('buffer');

// Tokenınızı Ortam Değişkeninden alın.
const token = '8350124542:AAHwsh0LksJAZOW-hHTY1BTu5i8-XKGFn18'; 

const bot = new TelegramBot(token, { polling: true });
console.log('Özel Lua Obfuscator Botu başlatılıyor...');

// ==============================================================================
// YARDIMCI İŞLEVLER
// ==============================================================================

/**
 * Rastgele bir string (değişken ismi) üretir.
 * @returns {string} Benzersiz bir isim
 */
function generateRandomName() {
    // Lua değişken ismi kurallarına uygun, okunması zor bir isim
    return '_' + Math.random().toString(36).substring(2) + Math.random().toString(36).substring(2);
}

// ==============================================================================
// LUA ÖZEL OBFUSCATION İŞLEVİ
// ==============================================================================

/**
 * Lua kodunu özel mantıkla obfuskate eder:
 * 1. Tüm local değişkenleri bulur.
 * 2. Yeni rastgele isimler atar.
 * 3. Tüm local tanımları kodun en başına taşır.
 * 4. Kalan kodu minifiye eder.
 * * @param {string} luaCode - Obfuskate edilecek Lua kodu.
 * @returns {string | null} Obfuskate edilmiş kod veya hata durumunda null.
 */
function customObfuscate(luaCode) {
    try {
        // 1. Kodu Minify Et (Yorum ve boşlukları temizle)
        let processedCode = luamin.minify(luaCode);

        // 2. Tüm local değişkenleri ve fonksiyon tanımlarını bul
        // Regex: local [a-zA-Z0-9_]+
        // Regex: local [a-zA-Z0-9_]+ = ...
        // Regex: local function [a-zA-Z0-9_]+
        
        // Basit local değişken bulucu (değişken ismi yakalanır)
        const localDeclarationsRegex = /local\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(=?)/g;
        
        const localNames = {}; // {orijinal_isim: yeni_isim}
        
        // Tüm local değişken ve fonksiyon isimlerini bul ve benzersiz isimler ata
        let match;
        while ((match = localDeclarationsRegex.exec(processedCode)) !== null) {
            const originalName = match[1];
            if (!localNames[originalName]) {
                 localNames[originalName] = generateRandomName();
            }
        }
        
        // 3. Kod içindeki tüm kullanımlarını yeni isimlerle değiştir
        let newCode = processedCode;
        const localHeader = [];

        // Önceki Regex ile tekrar değişken isimlerini bul ve global değiştirme yap
        for (const [originalName, newName] of Object.entries(localNames)) {
            // Değişkeni sadece kelime olarak değiştir (fonksiyon isimleri, metinler içindeki kelimeler değil)
            const replaceRegex = new RegExp(`\\b${originalName}\\b`, 'g');
            newCode = newCode.replace(replaceRegex, newName);
            
            // Başlık (Header) için local tanımını oluştur (varsayılan değer olmadan)
            localHeader.push(`local ${newName}`);
        }
        
        // 4. Tüm local tanımlarını koddan kaldır
        // Regex: ^local [a-zA-Z_][a-zA-Z0-9_]*(\s*=\s*.*?)?(\s*;)?\s*
        newCode = newCode.replace(/local\s+[a-zA-Z_][a-zA-Z0-9_]*(\s*=\s*.*?|\s*function\s*.*?|\s*function)?/g, '');


        // 5. Başa, rastgele isimlerle tanımlanmış local'leri ekle
        const finalHeader = `-- Obfuskasyon Tipi: Özel (Local Üste Çekme)\n` 
                          + `-- Bot: Telegram Advanced Obfuscator\n\n` 
                          + localHeader.join(';') + '\n\n';

        // newCode'u bir kez daha minify edelim, çünkü kaldırma işlemleri boşluk yaratmış olabilir
        const fullyMinifiedCode = luamin.minify(newCode);

        return finalHeader + fullyMinifiedCode;
        
    } catch (error) {
        console.error("Özel Obfuscation hatası:", error);
        return null;
    }
}

// ==============================================================================
// TELEGRAM BOT İŞLEVLERİ
// ==============================================================================

// /start komutu
bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    bot.sendMessage(
        chatId, 
        "🤖 **Özel Lua Obfuscator Botu** başlatıldı.\n\nBana obfuskate etmek istediğiniz **Lua kodunu doğrudan mesaj olarak** gönderin.\n\n⚙️ **Özel Mantık:**\n* Tüm local değişkenleriniz rastgele isimlerle değiştirilir.\n* Tüm local tanımları, kodun en üstüne çekilir."
    );
});

// Metin (Lua kodu) İşleyici
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;
    const isCommand = text && text.startsWith('/');

    if (text && !isCommand && !msg.photo && !msg.document) {
        
        await bot.sendMessage(chatId, "Kodunuz alınıyor ve **özel obfuskasyon** işlemi başlatılıyor...");

        // 1. Kodu obfuskate et
        const obfuscatedCode = customObfuscate(text);

        if (!obfuscatedCode) {
            await bot.sendMessage(chatId, "HATA: Girdiğiniz kod geçerli bir Lua kodu değil veya obfuskasyon sırasında beklenmedik bir hata oluştu. Lütfen kodu kontrol edin.");
            return;
        }

        // 2. Obfuskate edilmiş içeriği Buffer'a dönüştür (Dosya oluşturmak için)
        const outputBuffer = Buffer.from(obfuscatedCode, 'utf8');
        const newFileName = 'custom_obfuscated.lua';

        // 3. Dosya olarak geri gönder
        await bot.sendDocument(
            chatId,
            outputBuffer,
            { caption: 'İşte özel obfuskasyon çıktınız! Localler üste çekildi ve isimler değişti.' },
            { filename: newFileName, contentType: 'text/plain' }
        ).catch(error => {
            console.error("Dosya gönderme hatası:", error.message);
            bot.sendMessage(chatId, "Üzgünüm, obfuskasyon sonucunu dosya olarak gönderirken bir hata oluştu.");
        });
        
    } else if (isCommand && text !== '/start') {
         await bot.sendMessage(chatId, 'Bilinmeyen komut. Lütfen sadece Lua kodunu gönderin veya /start yazın.');
    } else if (msg.photo || msg.document) {
        await bot.sendMessage(chatId, "Lütfen sadece obfuskate etmek istediğiniz **metin** (Lua kodu) gönderin.");
    }
});
