import os
from aiogram import types, Bot
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from utils import format_duration, compress_video_to_target_size, cleanup_files, MAX_SIZE

def escape_html(text: str) -> str:
    """Escapes characters for HTML parsing."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def handle_twitter(message: types.Message, bot: Bot):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Please provide a Twitter/X URL after the command.\nExample: /x https://x.com/user/status/example")
        return
    url = parts[1].strip()

    status_msg = await message.reply("Downloading Twitter video... 📥")
    base_filename = f"twt_video_{message.from_user.id}_{message.message_id}"
    ydl_opts = {'outtmpl': f'{base_filename}.%(ext)s', 'format': 'best', 'quiet': True, 'no_warnings': True}

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if not file_path.endswith('.mp4'):
                new_path = f"{base_filename}.mp4"
                os.rename(file_path, new_path)
                file_path = new_path

        uploader = info.get('uploader', 'N/A')
        description = info.get('description', '')
        
        # Use the first line of the tweet as the title
        title = description.split('\n')[0]
        if len(title) > 200: title = title[:200] + '...'
            
        duration_seconds = info.get('duration', 0)

        caption = (f"🐦 <b>Tweet by:</b> {escape_html(uploader)}\n"
                   f"📝: {escape_html(title)}\n"
                   f"⏱ <b>Duration:</b> {format_duration(duration_seconds)}")
        
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