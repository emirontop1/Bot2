// bot.js

const TelegramBot = require('node-telegram-bot-api');
const luamin = require('luamin');
const axios = require('axios'); // Dosya indirmek için
const path = require('path');   // Dosya yolu işlemleri için

// Ortam değişkenini (Environment Variable) veya doğrudan token'ı kullanın
const token = '8350124542:AAHwsh0LksJAZOW-hHTY1BTu5i8-XKGFn18'; 

const bot = new TelegramBot(token, {polling: true});

console.log('Bot başlatıldı ve dosya işleme özelliğine sahip...');

// Telegram API dosya indirme URL'sinin temel kısmı
const FILE_BASE_URL = `https://api.telegram.org/file/bot${token}/`;

/**
 * Lua kodunu gizlemek (küçültmek) için ana işlev.
 */
function obfuscateLuaCode(luaCode) {
    try {
        const minifiedCode = luamin.minify(luaCode);
        return minifiedCode;
    } catch (error) {
        console.error('Lua kodunu gizlerken hata oluştu:', error.message);
        return null; // Başarısızlık durumunda null döndür
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
        "Merhaba! Ben Lua Kod Gizleme Botuyum. Bana gizlemek istediğiniz **Lua kod dosyasını (.lua)** gönderin. İçeriği gizleyip geri yollayacağım."
    );
});

// Dosya İşleyici
bot.on('document', async (msg) => {
    const chatId = msg.chat.id;
    const document = msg.document;

    // Sadece .lua uzantılı dosyaları kabul et
    const fileExtension = path.extname(document.file_name).toLowerCase();

    if (fileExtension !== '.lua') {
        bot.sendMessage(chatId, `Üzgünüm, sadece Lua dosyalarını (*.lua) işleyebilirim.`);
        return;
    }

    try {
        // 1. Telegram'dan dosya bilgisini al (file_path'i öğrenmek için)
        const file = await bot.getFile(document.file_id);
        const fileUrl = FILE_BASE_URL + file.file_path;

        // 2. Dosya içeriğini indir
        const response = await axios.get(fileUrl, { responseType: 'text' });
        const luaCode = response.data;

        console.log(`[${chatId}] '${document.file_name}' dosyası alındı ve indirildi.`);

        // 3. Kodu gizle (minify et)
        const obfuscatedCode = obfuscateLuaCode(luaCode);

        if (!obfuscatedCode) {
            bot.sendMessage(chatId, `HATA: ${document.file_name} dosyası geçerli bir Lua kodu değil veya gizleme sırasında hata oluştu.`);
            return;
        }

        // 4. Yeni dosya adı oluştur
        const originalName = path.basename(document.file_name, '.lua');
        const newFileName = `${originalName}_minified.lua`;

        // 5. Gizlenmiş içeriği dosya olarak geri yükle
        // Buffer'ı doğrudan Telegram'a göndermek en temiz yoldur
        const buffer = Buffer.from(obfuscatedCode, 'utf8');

        await bot.sendDocument(
            chatId,
            buffer,
            {}, // Opsiyonlar (boş bırakılabilir)
            {
                filename: newFileName,
                contentType: 'text/plain'
            }
        );

        console.log(`[${chatId}] '${newFileName}' dosyası başarıyla geri gönderildi.`);

    } catch (error) {
        console.error('Dosya işleme sırasında genel hata:', error.message);
        bot.sendMessage(chatId, `Dosyanızı işlerken beklenmedik bir hata oluştu. Lütfen daha sonra tekrar deneyin.`);
    }
});

// Komut dışı metinler
bot.on('message', (msg) => {
    if (msg.text && !msg.text.startsWith('/') && !msg.document) {
        bot.sendMessage(msg.chat.id, 'Lütfen doğrudan bir Lua dosyası gönderin.');
    }
});
