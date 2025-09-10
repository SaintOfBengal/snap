import qrcode
import io
from aiogram import types, Bot
from aiogram.types import BufferedInputFile

def escape_html(text: str) -> str:
    """Escapes characters for HTML parsing."""
    return text.replace("&", "&").replace("<", "<").replace(">", ">")

async def handle_qr(message: types.Message, bot: Bot):
    """
    Handles the /qr command to generate a QR code.
    """
    # Get the text to encode from the message, after the /qr command
    text_to_encode = message.text.replace("/qr", "").strip()

    if not text_to_encode:
        await message.reply("Please provide text or a link after the command.\n"
                            "<b>Example:</b> /qr https://telegram.org")
        return

    # Generate the QR code image
    qr_img = qrcode.make(text_to_encode)

    # Save the image to an in-memory buffer instead of a file
    with io.BytesIO() as buffer:
        qr_img.save(buffer, format="PNG")
        buffer.seek(0) # Go to the beginning of the buffer
        
        # Create an object that aiogram can send
        file_to_send = BufferedInputFile(buffer.getvalue(), filename="qr_code.png")

        # Send the photo
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=file_to_send,
            caption=f"✅ Here is the QR Code for:\n<code>{escape_html(text_to_encode)}</code>"
        )