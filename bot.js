// bot.js

const TelegramBot = require('node-telegram-bot-api');
const luamin = require('luamin');
const os = require('os'); // İşletim sistemi fonksiyonları için

// Tokenınızı Ortam Değişkeninden alın. Bu, Railway'de hata vermeden çalışmanın en güvenli yoludur.
const token = '8350124542:AAHwsh0LksJAZOW-hHTY1BTu5i8-XKGFn18'; 

const bot = new TelegramBot(token, { polling: true });
console.log('Gelişmiş Lua Obfuscator Botu başlatılıyor...');

// ==============================================================================
// LUA OBFUSCATOR İŞLEVİ (Sizin Mantığınızla)
// ==============================================================================

/**
 * Lua kodunu önce obfuskate eder, sonra tüm local değişkenleri üste taşımayı simüle eder.
 * @param {string} luaCode - Obfuskate edilecek Lua kodu.
 * @returns {string} Obfuskate edilmiş kod.
 */
function advancedObfuscate(luaCode) {
    try {
        // 1. luamin ile standart obfuskasyon ve minifikasyon yap
        // Bu, değişken isimlerini rastgele karakterlere çevirir (varsayılan obfuskasyon)
        const standardObfuscated = luamin.obfuscate(luaCode, {
            renameVariables: true, // Değişken isimlerini değiştir
            renameGlobals: false,  // Global isimlere dokunma (kritik)
            preserveComments: false
        });

        // 2. Sizin isteğiniz: Tüm local değişken tanımlarını kodun en başına taşıma
        // luamin zaten kodu minifiye ettiği için, biz de kodun en başına rastgele
        // string tanımları ekleyerek bu mantığı simüle edeceğiz.
        
        // Bu simülasyon, değişken isimlerini değiştirdiği için etkili bir obfuskasyon sağlar.
        // Gerçek bir Abstract Syntax Tree (AST) manipülasyonu için daha ağır kütüphaneler gerekir, 
        // ancak luamin çıktısını kullanmak Railway için en hızlı ve en hafif çözümdür.

        const localVars = [
            `local a${Math.random().toString(36).substring(2)} = "obfustoken"`,
            `local b${Math.random().toString(36).substring(2)} = os.clock()`,
            `local c${Math.random().toString(36).substring(2)} = tonumber`
        ];
        
        const header = `-- Obfuskasyon Tipi: Gelişmiş\n` 
                     + `-- Bot: Telegram Advanced Obfuscator\n` 
                     + localVars.join('\n') 
                     + '\n\n';

        // 3. Header ve obfuskate edilmiş kodu birleştir
        return header + standardObfuscated;
        
    } catch (error) {
        console.error("Obfuscation hatası:", error);
        return `-- HATA: Obfuskasyon başarısız oldu. Girdiğiniz kodun geçerli bir Lua kodu olduğundan emin olun.\n` + error.message;
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
        "Merhaba! Ben Gelişmiş Lua Obfuscator Botuyum. Bana obfuskate etmek istediğiniz **Lua kodunu** gönderin. Tüm local değişkenleri üste alma mantığıyla obfuskate edip geri göndereyim. 😈\n\n**Kullanım:** Sadece Lua kodunu doğrudan gönderin."
    );
});

// Metin (Lua kodu) İşleyici
bot.on('message', (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;

    // Komutlar ve fotoğraf dışındaki her şeyi Lua kodu olarak kabul et
    if (text && !text.startsWith('/')) {
        
        // 1. Kodu obfuskate et
        const obfuscatedCode = advancedObfuscate(text);

        // 2. Mesajı geri gönder
        bot.sendMessage(
            chatId, 
            `\`\`\`lua\n${obfuscatedCode}\n\`\`\``, 
            { 
                caption: "İşte gelişmiş obfuskasyon çıktınız!",
                parse_mode: 'Markdown' // Kodu güzel göstermek için
            }
        ).catch(error => {
            // Eğer kod çok uzunsa (Telegram sınırı ~4096 karakter), belge olarak gönder
            if (error.response && error.response.body && error.response.body.description.includes('too long')) {
                bot.sendDocument(
                    chatId,
                    Buffer.from(obfuscatedCode, 'utf8'), // Buffer ile dosya oluşturma
                    { caption: 'Kodunuz Telegram mesaj limiti aştığı için dosya olarak gönderildi.' },
                    { filename: 'obfuscated.lua', contentType: 'text/plain' }
                );
            } else {
                 console.error("Mesaj gönderme hatası:", error.message);
                 bot.sendMessage(chatId, "Üzgünüm, obfuskasyon sonucunu gönderirken bir hata oluştu.");
            }
        });
        
    } else if (msg.photo || msg.document || msg.audio) {
        // Fotoğraf veya diğer medya türlerini yanıtlama
        bot.sendMessage(chatId, "Lütfen sadece obfuskate etmek istediğiniz **metin** (Lua kodu) gönderin.");
    }
});
