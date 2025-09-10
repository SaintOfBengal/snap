import os
from aiogram import types, Bot
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from utils import cleanup_files

def escape_html(text: str) -> str:
    """Escapes characters for HTML parsing."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def handle_youtube_audio(message: types.Message, bot: Bot):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Please provide a YouTube URL after the command.\nExample: /song http://googleusercontent.com/youtube.com/...")
        return
    url = parts[1].strip()

    status_msg = await message.reply("Downloading and converting to MP3... 🎶")
    base_filename = f"yta_{message.from_user.id}_{message.message_id}"

    ydl_opts = {
        'outtmpl': f'{base_filename}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best',
        'cookiefile': 'youtube_cookies.txt', # Using YouTube-specific cookies
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = f"{base_filename}.mp3"
        
        title = info.get('title', 'Unknown Title')
        artist = info.get('artist') or info.get('uploader', 'Unknown Artist')
        if len(title) > 200: title = title[:200] + '...'
        if len(artist) > 50: artist = artist[:50] + '...'

        audio_to_send = FSInputFile(file_path, filename=f"{artist} - {title}.mp3")
        await bot.send_audio(
            message.chat.id,
            audio=audio_to_send,
            caption=f"🎵 <b>{escape_html(title)}</b>",
            parse_mode="HTML"
        )
        await status_msg.delete()
        cleanup_files(file_path)
    except Exception as e:
        await status_msg.delete()
        await message.reply(f"❌ An error occurred:\n<code>{escape_html(str(e))}</code>", parse_mode="HTML")
        cleanup_files(f"{base_filename}.mp3")