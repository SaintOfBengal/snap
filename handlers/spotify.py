import os
import aiohttp
from bs4 import BeautifulSoup
from aiogram import types, Bot
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from utils import cleanup_files, format_duration

def escape_html(text: str) -> str:
    """Escapes characters for HTML parsing."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def handle_spotify(message: types.Message, bot: Bot):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Please provide a Spotify Track URL after the command.\nExample: /sp <spotify_track_url>")
        return
    url = parts[1].strip()

    status_msg = await message.reply("Fetching Spotify track info... ℹ️")

    try:
        # Step 1: Scrape Spotify page to get the song title
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status != 200:
                    raise ValueError(f"Spotify returned a non-200 status code: {response.status}")
                html = await response.text()
        
        soup = BeautifulSoup(html, 'lxml')
        title_tag = soup.find('title')
        if not title_tag:
            raise ValueError("Could not find the title of the song on the page.")
            
        page_title = title_tag.text.replace("| Spotify", "").strip()

        await status_msg.edit_text(f"Found \"{page_title}\". Downloading from Spotify 𝟯𝟮𝟬 𝗞𝗕𝗣𝗦 (𝗢𝗴𝗴 𝗩𝗼𝗿𝗯𝗶𝘀) Quality... 🎵")
        
        # Step 2: Use yt-dlp to search and download the song from YouTube
        base_filename = f"spotify_{message.from_user.id}_{message.message_id}"
        search_query = f"ytsearch1:{page_title} official audio"

        audio_dl_opts = {
            'outtmpl': f'{base_filename}.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'cookiefile': 'cookies.txt',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with YoutubeDL(audio_dl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if not info.get('entries'):
                raise ValueError("Could not find a matching song on YouTube.")
            
            yt_title = info['entries'][0].get('title', 'Unknown Title')
            yt_artist = info['entries'][0].get('channel', 'Unknown Artist')
            duration_sec = info['entries'][0].get('duration', 0)
            file_path = f"{base_filename}.mp3"

        duration_formatted = format_duration(duration_sec)
        caption = (f"🎵 <b>Title:</b> {escape_html(yt_title)}\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"👤 <b>Artist:</b> {escape_html(yt_artist)}\n"
                   f"⏱ <b>Duration:</b> {duration_formatted}\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"Downloaded By: {escape_html(message.from_user.full_name)}")

        audio_to_send = FSInputFile(file_path, filename=f"{yt_artist} - {yt_title}.mp3")
        await bot.send_audio(
            message.chat.id,
            audio=audio_to_send,
            caption=caption,
            parse_mode="HTML"
        )
        await status_msg.delete()
        cleanup_files(file_path)
    except Exception as e:
        await status_msg.delete()
        await message.reply(f"❌ An error occurred:\n<code>{escape_html(str(e))}</code>\n\nNote: Only individual tracks are supported.", parse_mode="HTML")