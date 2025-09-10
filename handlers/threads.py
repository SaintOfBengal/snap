import os
from aiogram import types, Bot
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from utils import cleanup_files, format_duration

def escape_html(text: str) -> str:
    """Escapes characters for HTML parsing."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def handle_threads(message: types.Message, bot: Bot):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Please provide a Threads URL after the command.\nExample: /tdl https://www.threads.net/...")
        return
        
    url = parts[1].strip().split('?')[0]

    status_msg = await message.reply("Downloading Threads video... ⏳")
    base_filename = f"threads_{message.from_user.id}_{message.message_id}"
    
    ydl_opts = {
        'outtmpl': f'{base_filename}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'instagram_cookies.txt', # Using Instagram cookies for Threads
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        
        uploader = info.get('uploader', 'N/A')
        duration_seconds = info.get('duration', 0)
        
        caption = (f"🔗 <b>Source:</b> <a href='{url}'>View on Threads</a>\n"
                   f"👤 <b>Uploader:</b> {escape_html(uploader)}\n"
                   f"⏱ <b>Duration:</b> {format_duration(duration_seconds)}")
        
        video_to_send = FSInputFile(file_path)
        await bot.send_video(message.chat.id, video=video_to_send, caption=caption, parse_mode="HTML", request_timeout=120)
        await status_msg.delete()
        cleanup_files(file_path)

    except Exception as e:
        await status_msg.delete()
        safe_error_message = escape_html(str(e))
        
        if "Unsupported URL" in safe_error_message:
            await message.reply("❌ **Unsupported URL.**\nThis link might be for a text-only post, a multi-image post, or a format I can't download. Please try a link to a single video.")
        else:
            await message.reply(f"❌ An error occurred:\n<code>{safe_error_message}</code>", parse_mode="HTML")
            
        cleanup_files(f"{base_filename}.mp4")