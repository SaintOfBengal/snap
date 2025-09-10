import os
from aiogram import types, Bot
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from utils import format_duration, compress_video_to_target_size, cleanup_files, MAX_SIZE

def escape_html(text: str) -> str:
    """Escapes characters for HTML parsing."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def handle_facebook(message: types.Message, bot: Bot):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Please provide a Facebook URL after the command.\nExample: /fb https://facebook.com/video/example")
        return
    url = parts[1].strip()

    status_msg = await message.reply("Downloading Facebook video... ⏳")
    base_filename = f"fb_video_{message.from_user.id}_{message.message_id}"

    # 👇 Get cookies file path from .env (or hardcode "fb_cookies.txt")
    fb_cookies = os.getenv("FB_COOKIES", "fb_cookies.txt")

    ydl_opts = {
        'outtmpl': f'{base_filename}.%(ext)s',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }

    # ✅ Only add cookies if file exists
    if os.path.exists(fb_cookies):
        ydl_opts['cookiefile'] = fb_cookies

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = f"{base_filename}.mp4"

        title = info.get('title', 'N/A')
        if len(title) > 250: 
            title = title[:250] + '...'
        
        view_count = info.get('view_count', 0)
        views = f"{view_count:,}" if view_count else "N/A"
        duration_seconds = info.get('duration', 0)
        
        caption = (
            f"🎵 <b>Title:</b> {escape_html(title)}\n"
            f"👁️‍🗨️ <b>Views:</b> {views}\n"
            f"⏱ <b>Duration:</b> {format_duration(duration_seconds)}"
        )

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
            await bot.send_video(
                message.chat.id,
                video=video_to_send,
                caption=caption,
                parse_mode="HTML",
                request_timeout=300
            )
            cleanup_files(file_path, compressed_path)
        else:
            video_to_send = FSInputFile(file_path)
            await bot.send_video(
                message.chat.id,
                video=video_to_send,
                caption=caption,
                parse_mode="HTML",
                request_timeout=300
            )
            cleanup_files(file_path)

        await status_msg.delete()
    except Exception as e:
        await status_msg.delete()
