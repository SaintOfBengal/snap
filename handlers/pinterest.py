import os
from aiogram import types, Bot
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from utils import format_duration, compress_video_to_target_size, cleanup_files, MAX_SIZE

def escape_html(text: str) -> str:
    """Escapes characters for HTML parsing."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def handle_pinterest(message: types.Message, bot: Bot):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Please provide a Pinterest Pin URL after the command.\nExample: /pn https://pinterest.com/pin/example")
        return
    url = parts[1].strip()

    status_msg = await message.reply("Downloading your Pin... 📌")
    base_filename = f"pin_{message.from_user.id}_{message.message_id}"
    
    ydl_opts = {
        'outtmpl': f'{base_filename}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'pinterest_cookies.txt', # Using Pinterest-specific cookies
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        title = info.get('title') or info.get('description') or 'Pinterest Content'
        if len(title) > 250: title = title[:250] + '...'

        uploader = info.get('uploader', 'N/A')
        is_video = info.get('duration') is not None

        if is_video:
            duration_seconds = info.get('duration', 0)
            caption = (f"📌 <b>Pin by:</b> {escape_html(uploader)}\n"
                       f"📝: {escape_html(title)}\n"
                       f"⏱ <b>Duration:</b> {format_duration(duration_seconds)}")

            if not file_path.endswith('.mp4'):
                 new_path = f"{base_filename}.mp4"
                 os.rename(file_path, new_path)
                 file_path = new_path

            file_size = os.path.getsize(file_path)
            if file_size > MAX_SIZE:
                await status_msg.edit_text("Compressing video... 🎥")
                compressed_path = f"{base_filename}_compressed.mp4"
                compress_video_to_target_size(file_path, compressed_path, duration_seconds)
                
                if os.path.getsize(compressed_path) > MAX_SIZE:
                    await status_msg.delete()
                    await message.reply("❌ Sorry, this video is too long to be compressed under 50MB.")
                    cleanup_files(file_path, compressed_path)
                    return

                video_to_send = FSInputFile(compressed_path)
                await bot.send_video(message.chat.id, video=video_to_send, caption=caption, parse_mode="HTML", request_timeout=300)
                cleanup_files(file_path, compressed_path)
            else:
                video_to_send = FSInputFile(file_path)
                await bot.send_video(message.chat.id, video=video_to_send, caption=caption, parse_mode="HTML", request_timeout=300)
                cleanup_files(file_path)
        else: # Handle images
            caption = (f"📌 <b>Pin by:</b> {escape_html(uploader)}\n"
                       f"📝: {escape_html(title)}")
            photo_to_send = FSInputFile(file_path)
            await bot.send_photo(message.chat.id, photo=photo_to_send, caption=caption, parse_mode="HTML")
            cleanup_files(file_path)

        await status_msg.delete()
    except Exception as e:
        await status_msg.delete()
        safe_error_message = escape_html(str(e))
        if "Unsupported URL" in safe_error_message:
             await message.reply("❌ This looks like a Pinterest board. Please provide a link to a specific Pin (video or image).")
        else:
            await message.reply(f"❌ An error occurred:\n<code>{safe_error_message}</code>", parse_mode="HTML")
        cleanup_files(f"{base_filename}.mp4")