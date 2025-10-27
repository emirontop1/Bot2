# 1. Adım: Temel işletim sistemi olarak Python'un güncel bir sürümünü kullan
FROM python:3.10-slim

# 2. Adım: Çalışma dizinini ayarla
WORKDIR /app

# 3. Adım: Tarayıcı ve sürücüyü kur (En önemli kısım)
# Google'ın resmi anahtarını ve deposunu ekleyerek güncel Chrome'u kuralım
# Not: Railway'in Debian tabanlı sistemleri için bu daha kararlıdır.
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    # Google Chrome deposunu ekle
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    # ChromeDriver'ı kur
    && apt-get update \
    && apt-get install -y google-chrome-stable chromedriver \
    # Gereksiz dosyaları temizle
    && rm -rf /var/lib/apt/lists/*

# 4. Adım: Python kütüphanelerini kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Adım: Bot kodunu konteynere kopyala
COPY bot.py .

# 6. Adım: Botu çalıştır
CMD ["python", "bot.py"]
