import os
import yt_dlp
from aiogram import types, Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils import format_duration, compress_video_to_target_size, cleanup_files, MAX_SIZE
from keyboards.callbacks import YouTubeCallback

def escape_html(text: str) -> str:
    """Escapes characters for HTML parsing."""
    return text.replace("&", "&").replace("<", "<").replace(">", ">")

# Handler #1: For the initial /yt command
async def handle_youtube(message: types.Message, bot: Bot):
    """
    Step 1: Fetches available formats for a YouTube URL and shows them as buttons.
    """
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Please provide a YouTube URL after the command.\nExample: `/yt <youtube_url>`")
        return
    url = parts[1].strip()
    
    status_msg = await message.reply("Fetching video details... 🔍")

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        video_id = info['id']
        builder = InlineKeyboardBuilder()
        
        added_resolutions = set()
        for f in info.get('formats', []):
            resolution = f.get('height')
            if resolution in [480, 720, 1080] and f.get('vcodec') != 'none' and f.get('ext') == 'mp4':
                if resolution not in added_resolutions:
                    # FIXED: Store the quality (e.g., "720") instead of a specific format_id
                    callback_data = YouTubeCallback(video_id=video_id, quality=str(resolution), ext='mp4').pack()
                    builder.button(
                        text=f"📹 {resolution}p (.mp4)",
                        callback_data=callback_data
                    )
                    added_resolutions.add(resolution)
        
        best_audio = next((f for f in info.get('formats', []) if f.get('vcodec') == 'none' and f.get('ext') == 'm4a'), None)
        if best_audio:
            # FIXED: Store 'audio' as the quality
            callback_data = YouTubeCallback(video_id=video_id, quality='audio', ext='mp3').pack()
            builder.button(
                text=f"🎵 Audio Only (.mp3)",
                callback_data=callback_data
            )
            
        builder.adjust(2)
        
        if not builder.buttons:
             await status_msg.edit_text("❌ No suitable download formats found for this video.")
             return

        await status_msg.edit_text(
            f"✅ Found video: <b>{escape_html(info.get('title', ''))}</b>\n\nPlease select a format to download:",
            reply_markup=builder.as_markup()
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ An error occurred:\n<code>{escape_html(str(e))}</code>")


# Handler #2: For the callback query when a user clicks a button
async def youtube_quality_callback(callback: types.CallbackQuery, bot: Bot):
    """
    Step 2: Handles the download after a user selects a quality.
    """
    callback_data = YouTubeCallback.unpack(callback.data)
    video_id = callback_data.video_id
    quality = callback_data.quality
    extension = callback_data.ext
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    await callback.message.edit_text(f"Starting download... ⏳ This may take a moment.")
    
    base_filename = f"yt_{callback.from_user.id}_{video_id}"
    
    # --- FIXED ---
    # This now uses yt-dlp's powerful format selection strings for a more reliable download.
    if quality == 'audio':
        download_format = 'bestaudio/best'
    else:
        download_format = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]'
    
    ydl_opts = {
        'outtmpl': f'{base_filename}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'format': download_format,
        'merge_output_format': 'mp4',
        'cookiefile': 'youtube_cookies.txt',
    }

    if extension == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        
        # Determine the final file path after download
        # The actual extension might be different from what we requested (e.g., .m4a -> .mp3)
        # So we find the file that was actually created.
        final_path = None
        for ext in [extension, 'm4a', 'mp4']: # Check for possible output extensions
            potential_path = f"{base_filename}.{ext}"
            if os.path.exists(potential_path):
                final_path = potential_path
                break
        
        if not final_path:
            raise FileNotFoundError("Downloaded file could not be found.")

        # Rename the file to the expected final extension for consistency
        if final_path != f"{base_filename}.{extension}":
            os.rename(final_path, f"{base_filename}.{extension}")
        
        file_path = f"{base_filename}.{extension}"
        
        if extension == 'mp3':
            title = info.get('title', 'Unknown Title')
            artist = info.get('artist') or info.get('uploader', 'Unknown Artist')
            audio_to_send = FSInputFile(file_path, filename=f"{artist} - {title}.mp3")
            await bot.send_audio(callback.message.chat.id, audio=audio_to_send, caption=f"🎵 <b>{escape_html(title)}</b>")
        
        else: # Handle Video
            caption = f"✅ <b>{escape_html(info.get('title', 'N/A'))}</b>"
            file_size = os.path.getsize(file_path)

            if file_size > MAX_SIZE:
                await callback.message.edit_text("File is large, compressing... 🎥")
                compressed_path = f"{base_filename}_compressed.mp4"
                duration_seconds = info.get('duration', 0)
                compress_video_to_target_size(file_path, compressed_path, duration_seconds)

                if os.path.getsize(compressed_path) > MAX_SIZE:
                    await callback.message.edit_text("❌ Sorry, this video is too long to be compressed under 50MB.")
                    cleanup_files(file_path, compressed_path)
                    return
                
                video_to_send = FSInputFile(compressed_path)
                await bot.send_video(callback.message.chat.id, video=video_to_send, caption=caption)
                cleanup_files(file_path, compressed_path)
            else:
                video_to_send = FSInputFile(file_path)
                await bot.send_video(callback.message.chat.id, video=video_to_send, caption=caption)
                cleanup_files(file_path)

        await callback.message.delete()

    except Exception as e:
        await callback.message.edit_text(f"❌ An error occurred during download:\n<code>{escape_html(str(e))}</code>")
        cleanup_files(f"{base_filename}.mp4", f"{base_filename}.mp3", f"{base_filename}.m4a", f"{base_filename}_compressed.mp4")