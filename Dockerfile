# Dockerfile - Lua 5.4 + luarocks + gerekli rocks
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget build-essential unzip ca-certificates curl git \
    lua5.4 lua5.4-dev luarocks \
    && rm -rf /var/lib/apt/lists/*

# Ensure luarocks uses lua5.4 (debian's luarocks usually already configured)
RUN luarocks install luasocket || true
RUN luarocks install dkjson || true

WORKDIR /app
COPY . /app

EXPOSE 8080

# Use lua5.4 explicitly so we don't depend on 'lua' symlink
CMD ["lua5.4", "main.lua"]
