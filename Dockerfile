# Daha stabil ve küçük bir taban imajı kullanın
FROM python:3.10-slim

# Eksik olan iki sistem kütüphanesini (libGL.so.1 ve libgthread-2.0.so.0) kurun.
# libgl1 -> libGL.so.1'i sağlar
# libglib2.0-0 -> libgthread-2.0.so.0'ı sağlar
RUN apt-get update && \
    apt-get install -y libgl1 libglib2.0-0 && \
    # Kurulum sonrası önbelleği temizleyerek imaj boyutunu küçültün
    rm -rf /var/lib/apt/lists/*

# Uygulamanızın geri kalanını kurun
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Botunuzu başlatma komutu
CMD ["python", "bot.py"]
