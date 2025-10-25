from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from io import BytesIO
from PIL import Image

BOT_TOKEN = "8350124542:AAHwsh0LksJAZOW-hHTY1BTu5i8-XKGFn18"

def rgb_to_lua_color(r, g, b):
    return f"Color3.fromRGB({r}, {g}, {b})"

def image_to_lua(img: Image.Image, scale: int = 1):
    w, h = img.size
    pixels = img.load()

    lines = [
        'local screenGui = Instance.new("ScreenGui")',
        'screenGui.Name = "GeneratedImage"',
        'screenGui.ResetOnSpawn = false',
        'screenGui.Parent = game:GetService("Players").LocalPlayer:WaitForChild("PlayerGui")',
        ''
    ]

    for y in range(h):
        for x in range(w):
            r, g, b, *a = pixels[x, y]
            alpha = a[0] if a else 255
            if alpha < 5:
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

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    bio = BytesIO()
    await file.download_to_memory(out=bio)
    bio.seek(0)

    img = Image.open(bio).convert("RGBA")
    img.thumbnail((64, 64))
    lua_code = image_to_lua(img, scale=2)

    with open("output.lua", "w", encoding="utf-8") as f:
        f.write(lua_code)

    await update.message.reply_document(
        document=open("output.lua", "rb"),
        filename="output.lua"
    )

    await update.message.reply_text(
        f"Görsel dönüştürüldü: {img.size[0]}x{img.size[1]}"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

if __name__ == "__main__":
    app.run_polling()
