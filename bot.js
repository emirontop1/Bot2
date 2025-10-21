// bot.js

const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const Jimp = require('jimp');
const faceapi = require('face-api.js');
const tf = require('@tensorflow/tfjs-node'); // face-api.js'i Node.js ortamında çalıştırmak için gerekli
const path = require('path');
const { Buffer } = require('buffer');

// Bot Token'ınızı veya Ortam Değişkeninizi kullanın
const token = '8350124542:AAHwsh0LksJAZOW-hHTY1BTu5i8-XKGFn18'; 

const bot = new TelegramBot(token, { polling: true });
console.log('Face-API.js Yüz Sansürleme Botu başlatılıyor...');

const FILE_BASE_URL = `https://api.telegram.org/file/bot${token}/`;

// Modelleri belleğe yükle
async function loadModels() {
    console.log("Face-API modelleri yükleniyor...");
    // Sadece yüz tespiti için gerekli olan SSD Mobilenet V1 modelini yüklüyoruz.
    await faceapi.nets.ssdMobilenetv1.loadFromDisk('./node_modules/face-api.js/model'); 
    console.log("Modeller başarıyla yüklendi.");
}

// Global olarak modellerin yüklenmesini bekle
loadModels().catch(err => {
    console.error("Modeller yüklenirken kritik hata:", err);
    process.exit(1);
});

/**
 * Görseldeki yüzleri tespit eder ve sansürler.
 * @param {Buffer} imageBuffer - Görselin Buffer verisi
 * @returns {Buffer | null} Sansürlenmiş görselin Buffer verisi veya null
 */
async function censorFaces(imageBuffer) {
    try {
        // 1. Jimp ile görseli yükle
        const jimpImage = await Jimp.read(imageBuffer);
        
        // 2. Jimp görselini face-api.js'in işleyebileceği Tensör'e dönüştür
        const tensor = tf.node.tensor3d(
            Uint8Array.from(jimpImage.bitmap.data), 
            [jimpImage.bitmap.height, jimpImage.bitmap.width, 4], 
            'int32'
        ).slice([0, 0, 0], [-1, -1, 3]); // RGBA'dan RGB'ye kes

        // 3. Yüzleri tespit et
        const detections = await faceapi.detectAllFaces(
            tensor, 
            new faceapi.SsdMobilenetv1Options()
        );
        
        // Bellek yönetimi: Tensör'ü serbest bırak
        tf.dispose(tensor); 

        if (detections.length === 0) {
            return null; // Yüz bulunamadı
        }

        // 4. Tespit edilen yüzler üzerine siyah kare çiz
        detections.forEach(detection => {
            const box = detection.box;
            
            // Sansürleme Alanı (siyah kare)
            jimpImage.scan(
                box.x, box.y, // Başlangıç X, Y
                box.width, box.height, // Genişlik, Yükseklik
                function (x, y, idx) {
                    this.bitmap.data[idx + 0] = 0; // Kırmızı (R)
                    this.bitmap.data[idx + 1] = 0; // Yeşil (G)
                    this.bitmap.data[idx + 2] = 0; // Mavi (B)
                    // Opaklık (A) değiştirilmez
                }
            );
        });

        // 5. İşlenmiş görseli tekrar Buffer'a dönüştür
        const censoredBuffer = await jimpImage.getBufferAsync(Jimp.MIME_JPEG);
        return censoredBuffer;

    } catch (error) {
        console.error('Yüz tespiti veya sansürleme sırasında hata:', error);
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
        "Merhaba! Node.js ve yapay zeka ile çalışan yüz sansürleme botuyum. Bana bir **fotoğraf** gönderin, üzerindeki tüm yüzleri otomatik olarak sansürleyip geri göndereyim. 😈"
    );
});

// Fotoğraf İşleyici
bot.on('photo', async (msg) => {
    const chatId = msg.chat.id;
    const photoArray = msg.photo;
    
    // En yüksek çözünürlüklü fotoğrafı al
    const photo = photoArray[photoArray.length - 1]; 

    try {
        await bot.sendMessage(chatId, "Fotoğraf alınıyor ve yüzler tespit ediliyor...");
        
        // 1. Telegram'dan dosya bilgisini al
        const file = await bot.getFile(photo.file_id);
        const fileUrl = FILE_BASE_URL + file.file_path;

        // 2. Görsel içeriğini indir (Buffer olarak)
        const response = await axios.get(fileUrl, { responseType: 'arraybuffer' });
        const imageBuffer = Buffer.from(response.data);

        // 3. Yüzleri sansürle
        const censoredBuffer = await censorFaces(imageBuffer);

        if (censoredBuffer) {
            // 4. Sansürlenmiş fotoğrafı geri gönder
            await bot.sendPhoto(
                chatId,
                censoredBuffer,
                { caption: "İşte sansürlenmiş fotoğrafınız! Tüm yüzler kapatıldı. 🤐" }
            );
        } else {
            await bot.sendMessage(chatId, "Fotoğrafta yüz tespit edilemedi veya bir hata oluştu. Lütfen daha net bir görsel deneyin.");
        }

    } catch (error) {
        console.error('Görsel işleme sırasında genel hata:', error.message);
        bot.sendMessage(chatId, `Görselinizi işlerken beklenmedik bir hata oluştu: ${error.message}`);
    }
});

// Diğer mesajlar için bilgilendirme
bot.on('message', (msg) => {
    if (msg.text && !msg.text.startsWith('/') && !msg.photo) {
        bot.sendMessage(msg.chat.id, 'Lütfen doğrudan bir **fotoğraf** gönderin. Sansürleme işlemi için metin komutları gerekmez.');
    }
});
