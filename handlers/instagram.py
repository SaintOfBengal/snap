import os
from aiogram import types, Bot
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from utils import format_duration, compress_video_to_target_size, cleanup_files, MAX_SIZE

def escape_html(text: str) -> str:
    """Escapes characters for HTML parsing."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def handle_instagram(message: types.Message, bot: Bot):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Please provide an Instagram URL after the command.\nExample: /ig https://instagram.com/p/example")
        return
    url = parts[1].strip()

    status_msg = await message.reply("Downloading Instagram video... 📥")
    base_filename = f"ig_video_{message.from_user.id}_{message.message_id}"
    ydl_opts = {'outtmpl': f'{base_filename}.%(ext)s', 'format': 'best', 'quiet': True, 'no_warnings': True}

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            # Ensure the file has a .mp4 extension for consistency
            if not file_path.endswith('.mp4'):
                new_path = f"{base_filename}.mp4"
                os.rename(file_path, new_path)
                file_path = new_path

        title = info.get('title', 'Instagram Post')
        if len(title) > 250: title = title[:250] + '...'
            
        duration_seconds = info.get('duration', 0)
        
        caption = f"📸 <b>{escape_html(title)}</b>\n⏱ <b>Duration:</b> {format_duration(duration_seconds)}"

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

        await status_msg.delete()
    except Exception as e:
        await status_msg.delete()
        await message.reply(f"❌ An error occurred:\n<code>{escape_html(str(e))}</code>", parse_mode="HTML")
        cleanup_files(f"{base_filename}.mp4", f"{base_filename}_compressed.mp4")