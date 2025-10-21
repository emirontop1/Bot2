// bot.js

const TelegramBot = require('node-telegram-bot-api');
const luamin = require('luamin'); // Lua Minifier (Node.js paketi)

// Lütfen buraya kendi Telegram Bot Token'ınızı girin.
// Veya Railway'de Environment Variable (Ortam Değişkeni) olarak ayarlayın.
const token = '8350124542:AAHwsh0LksJAZOW-hHTY1BTu5i8-XKGFn18'; 

// Bot örneğini oluştur
const bot = new TelegramBot(token, {polling: true});

console.log('Bot başlatılıyor...');

/**
 * Lua kodunu gizlemek (küçültmek) için kullanılan ana işlev.
 */
function obfuscateLuaCode(luaCode) {
    try {
        const minifiedCode = luamin.minify(luaCode);
        return minifiedCode;
    } catch (error) {
        console.error('Lua kodunu gizlerken hata oluştu:', error.message);
        return `HATA: Kod gizlenirken bir sorun oluştu. Kodun geçerli bir Lua kodu olduğundan emin olun. Detay: ${error.message}`;
    }
}

// /start komutu
bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    bot.sendMessage(
        chatId, 
        "Merhaba! Ben Node.js ile yazılmış Lua Kod Gizleme Botuyum. Bana gizlemek istediğiniz Lua kodunu `/minify [KOD]` komutu ile gönderin."
    );
});

// /minify komutu
bot.onText(/\/minify (.+)/, (msg, match) => {
    const chatId = msg.chat.id;
    const luaCode = match[1]; 

    console.log(`[${chatId}] Gizlenecek kod alındı: ${luaCode.substring(0, 50)}...`);

    const obfuscatedCode = obfuscateLuaCode(luaCode);

    if (obfuscatedCode.startsWith('HATA:')) {
        bot.sendMessage(chatId, obfuscatedCode);
    } else {
        // Kodu Markdown ile gönder
        bot.sendMessage(
            chatId, 
            `**Gizlenmiş Lua Kodu:**\n\`\`\`lua\n${obfuscatedCode}\n\`\`\``,
            { parse_mode: 'Markdown' }
        );
    }
});

// Diğer mesajları bilgilendirme
bot.on('message', (msg) => {
    const chatId = msg.chat.id;
    if (msg.text && !msg.text.startsWith('/') && !msg.reply_to_message) {
        bot.sendMessage(chatId, 'Lütfen kodu `/minify [KODUNUZ]` formatında gönderin veya `/start` yazarak yardım alın.');
    }
});
