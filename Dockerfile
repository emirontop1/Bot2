# Kullanımı kolay, stabil bir temel: Debian
FROM debian:bookworm-slim

# Sistem araçları + lua + luarocks
RUN apt-get update && apt-get install -y --no-install-recommends \
    lua5.4 \
    luarocks \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Gerekli Lua rock'larını yüklüyoruz (socket + dkjson örneği)
RUN luarocks install luasocket || true
RUN luarocks install dkjson || true

# Uygulamayı kopyala
WORKDIR /app
COPY . /app

EXPOSE 8080

# Varsayılan komut: main.lua çalıştır
CMD ["lua", "main.lua"]
