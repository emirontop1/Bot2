# Daha stabil ve küçük bir taban imajı kullanın.
FROM python:3.10-slim

# libGL.so.1 bağımlılığını (OpenCV için gerekli) sistem düzeyinde kurun.
# Bu, hatayı kesin olarak çözecektir.
# Eksik olan libGL.so.1 kütüphanesini sağlayan güncel Debian paketini kurun.
RUN apt-get update && \
    apt-get install -y libgl1 && \
    rm -rf /var/lib/apt/lists/*

# Çalışma dizinini belirleyin.
WORKDIR /app

# Python bağımlılıklarını kurmak için requirements.txt dosyasını kopyalayın.
COPY requirements.txt .

# Python bağımlılıklarını kurun.
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarının geri kalanını konteynere kopyalayın.
COPY . .

# Botunuzu başlatma komutu. bot.py dosyasını çalıştırmasını söylüyoruz.
CMD ["python", "bot.py"]
