# bot.py
import os
import io
import logging
import tempfile
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# CONFIG
TELEGRAM_TOKEN = "8280902341:AAEQvYIlhpBfcI8X6KviiWkzIck-leeoqHU"  # set this in Railway or your env
# If image has more pixels than MAX_PIXELS, it will be resized keeping aspect ratio
MAX_PIXELS = 2_000_000  # 2 million default safety limit
MAX_EDGE = 1024         # max width/height if we need to downscale
FORCE_FULL_PIXELS = False  # set True to ignore the safety limit (risky)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Pixel→HTML Bot'a hoş geldiniz.\n"
        "Bir görsel gönderin; ben her pikselini HTML'ye çevirip .html dosyası olarak geri göndereceğim."
    )

def pil_resize_if_needed(img: Image.Image) -> (Image.Image, bool):
    """Check pixel count and optionally resize. Returns (image, resized_flag)."""
    w, h = img.size
    pixels = w * h
    if FORCE_FULL_PIXELS:
        return img, False
    if pixels <= MAX_PIXELS:
        return img, False
    # need to downscale keeping aspect ratio to keep under MAX_PIXELS but also limit edge
    # compute scale by edge limit first
    scale = 1.0
    if max(w, h) > MAX_EDGE:
        scale = MAX_EDGE / max(w, h)
        w_new = int(w * scale)
        h_new = int(h * scale)
    else:
        # scale to reduce pixel count
        scale = (MAX_PIXELS / pixels) ** 0.5
        w_new = max(1, int(w * scale))
        h_new = max(1, int(h * scale))
    img2 = img.resize((w_new, h_new), Image.LANCZOS)
    return img2, True

def image_to_html_table(img: Image.Image) -> str:
    """Converts a PIL image to an HTML string containing a table where each cell is 1px colored."""
    # ensure RGB
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    pixels = list(img.getdata())  # row-major
    # Build HTML incrementally (memory heavy for huge images, but acceptable for moderate sizes)
    html_parts = []
    html_parts.append("<!doctype html>")
    html_parts.append("<html><head><meta charset='utf-8'><title>Image → HTML (pixel table)</title>")
    # minimal CSS
    css = (
        "<style>"
        "table{border-collapse:collapse; image-rendering: pixelated;}"
        "td{width:1px; height:1px; padding:0; margin:0; border:0;}"
        "body{background:#111; display:flex; justify-content:center; align-items:center;}"
        "</style>"
    )
    html_parts.append(css)
    html_parts.append("</head><body>")
    html_parts.append("<table>")

    # write rows
    idx = 0
    for y in range(h):
        html_parts.append("<tr>")
        row_cells = []
        for x in range(w):
            r, g, b = pixels[idx]
            idx += 1
            # convert to hex color
            hexc = f"#{r:02x}{g:02x}{b:02x}"
            # use inline style background-color
            row_cells.append(f"<td style='background:{hexc}'></td>")
        html_parts.append("".join(row_cells))
        html_parts.append("</tr>")
    html_parts.append("</table>")
    html_parts.append("</body></html>")
    return "\n".join(html_parts)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
    await message.reply_text("Görsel alındı. İşleniyor — biraz zaman alabilir...")
    # get best quality photo
    if message.photo:
        photo = message.photo[-1]
        file = await photo.get_file()
        bio = io.BytesIO()
        await file.download_to_memory(out=bio)
        bio.seek(0)
    elif message.document and message.document.mime_type.startswith("image/"):
        # if user sent as document (original), handle it
        file = await context.bot.get_file(message.document.file_id)
        bio = io.BytesIO()
        await file.download_to_memory(out=bio)
        bio.seek(0)
    else:
        await message.reply_text("Lütfen bir fotoğraf gönderin (ben fotoğrafları işliyorum).")
        return

    try:
        img = Image.open(bio)
    except Exception as e:
        logger.exception("Resim açılamadı")
        await message.reply_text(f"Resim açılamadı: {e}")
        return

    original_size = img.size
    img_proc, resized = pil_resize_if_needed(img)

    if resized:
        await message.reply_text(
            f"Uyarı: Görsel büyük olduğu için yeniden boyutlandırıldı. "
            f"Orijinal: {original_size[0]}x{original_size[1]}, Yeni: {img_proc.size[0]}x{img_proc.size[1]}"
        )

    await message.reply_text("HTML dosyası oluşturuluyor (bu işlem CPU ve RAM kullanabilir)...")

    # generate HTML
    try:
        html = image_to_html_table(img_proc)
    except MemoryError:
        await message.reply_text("Bellek hatası oluştu: görsel çok büyük. Daha küçük bir görsel deneyin.")
        return
    except Exception as e:
        logger.exception("HTML oluşturulurken hata")
        await message.reply_text(f"HTML oluşturulurken hata: {e}")
        return

    # write to a temporary file and send
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        tmp_name = tmp.name
        tmp.write(html.encode("utf-8"))
    # send document
    try:
        with open(tmp_name, "rb") as f:
            await message.reply_document(document=f, filename="image_pixels.html", caption="İşte HTML dosyanız — tarayıcıda açın.")
    finally:
        try:
            os.unlink(tmp_name)
        except Exception:
            pass

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fotoğraf gönderin; ben onu HTML'ye çevirip .html dosyası olarak geri gönderirim. /start ile bilgi alabilirsiniz.")

def main():
    if not TELEGRAM_TOKEN:
        print("ERROR: TELEGRAM_TOKEN environment variable not set.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | (filters.Document.IMAGE), handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot başlatılıyor (polling). CTRL+C ile durdurun.")
    app.run_polling()

if __name__ == "__main__":
    main()
