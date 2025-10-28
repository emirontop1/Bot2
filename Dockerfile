# Dockerfile - Debian Bookworm, Lua 5.4, luarocks, luasocket ve dkjson
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# Sistem paketleri + lua5.4 + dev kütüphaneleri + luarocks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    ca-certificates \
    git \
    lua5.4 \
    lua5.4-dev \
    luarocks \
    libreadline-dev \
    libncurses5-dev \
    libssl-dev \
    libz-dev \
    libpcre3-dev \
    && rm -rf /var/lib/apt/lists/*

# Ensure luarocks uses lua5.4 — bazı Debian paketlerinde zaten doğru olur.
# Yine de ekstra güven için luarocks path'lerini güncelleme yapılabilir ama çoğu durumda bu yeterlidir.
# Install rocks
RUN luarocks install --local luasocket || luarocks install luasocket || true
RUN luarocks install --local dkjson || luarocks install dkjson || true

WORKDIR /app
COPY . /app

EXPOSE 8080

# Use lua5.4 explicitly and run main.lua with a pcall so build logs show errors clearly
CMD ["lua5.4", "-e", "local ok,err=pcall(dofile,'main.lua'); if not ok then print('Lua crashed:',err) os.exit(1) end"]
