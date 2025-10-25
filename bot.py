# bot.py
# Telegram botu: fotoğrafı alır ve piksel bazlı Lua GUI koduna çevirir.
# Kullanım:
# 1) BOT_TOKEN kısmına kendi token'ını yaz.
# 2) pip install -r requirements.txt
# 3) python bot.py
# 4) Telegram'dan bota fotoğraf gönder. Geriye output.lua dosyası döner.

from telegram import Update, Bot
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from io import BytesIO
from PIL import Image

BOT_TOKEN = "8350124542:AAHwsh0LksJAZOW-hHTY1BTu5i8-XKGFn18"

def rgb_to_lua_color(r, g, b):
    return f"Color3.fromRGB({r}, {g}, {b})"

def image_to_lua(img: Image.Image, scale: int = 1):
    w, h = img.size
    pixels = img.load()

    lines = []
    lines.append('local screenGui = Instance.new("ScreenGui")')
    lines.append('screenGui.Name = "GeneratedImage"')
    lines.append('screenGui.ResetOnSpawn = false')
    lines.append('screenGui.Parent = game:GetService("Players").LocalPlayer:WaitForChild("PlayerGui")')

    lines.append('')

    for y in range(h):
        for x in range(w):
            r, g, b, *a = pixels[x, y]
            alpha = a[0] if a else 255
            if alpha < 5:  # saydam pikseli atla
                continue
            color = rgb_to_lua_color(r, g, b)
            lines.append('do')
            lines.append('    local f = Instance.new("Frame")')
            lines.append(f'    f.Size = UDim2.new(0, {scale}, 0, {scale})')
            lines.append(f'    f.Position = UDim2.new(0, {x * scale}, 0, {y * scale})')
            lines.append(f'    f.BackgroundColor3 = {color}')
            lines.append('    f.BorderSizePixel = 0')
            lines.append('    f.Parent = screenGui')
            lines.append('end')

    return "\n".join(lines)

def handle_photo(update: Update, context: CallbackContext):
    photo = update.message.photo[-1]
    file = photo.get_file()
    bio = BytesIO()
    file.download(out=bio)
    bio.seek(0)

    img = Image.open(bio).convert("RGBA")
    max_side = 64  # kalite + boyut dengesi
    img.thumbnail((max_side, max_side))

    lua_code = image_to_lua(img, scale=2)

    with open("output.lua", "w", encoding="utf-8") as f:
        f.write(lua_code)

    with open("output.lua", "rb") as f:
        context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename="output.lua")

    update.message.reply_text(f"Görsel başarıyla Lua GUI koduna dönüştürüldü ({img.size[0]}x{img.size[1]}).")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
