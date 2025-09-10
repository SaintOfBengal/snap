from aiogram import F
from aiogram.types import Message, CallbackQuery
from keyboards.inline import get_start_keyboard, get_main_menu_keyboard, get_downloader_menu_keyboard
from aiogram.filters import CommandStart

async def start_handler(message: Message):
    user_name = message.from_user.full_name
    
    welcome_text = (
        f"Hi, <b>{user_name}</b>! Welcome to this bot.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "This bot is your ultimate toolkit on Telegram, packed with AI tools, educational resources, downloaders, temp mail, crypto utilities, and more. Simplify your tasks with ease!\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Don't forget to <a href='https://t.me/your_channel_username'>join</a> for updates!"
    )
    
    await message.answer(
        text=welcome_text,
        reply_markup=get_start_keyboard(),
        disable_web_page_preview=True
    )

async def main_menu_handler(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "Here are the Smart-Util Options: 👇",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception:
        await callback.answer("Already at the Main Menu.")
    await callback.answer()

async def menu_page_handler(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(
        reply_markup=get_main_menu_keyboard(page)
    )
    await callback.answer()

async def about_me_handler(callback: CallbackQuery):
    about_text = (
        "<b>About This Bot</b>\n\n"
        "This is a powerful media downloader bot created to make your life easier. "
        "Built with Python and Aiogram by an awesome developer!"
    )
    await callback.message.answer(about_text, disable_web_page_preview=True)
    await callback.answer()

async def policy_terms_handler(callback: CallbackQuery):
    policy_text = (
        "<b>Policy & Terms of Service</b>\n\n"
        "1. This bot is for personal use only.\n"
        "2. Do not use this bot to download copyrighted material without permission.\n"
        "3. The developers are not responsible for how you use this bot."
    )
    await callback.message.answer(policy_text)
    await callback.answer()

async def close_menu_handler(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

async def downloaders_menu_handler(callback: CallbackQuery):
    text = """
<b>Social Media and Music Downloader</b>

<b>USAGE:</b>
Download videos and tracks from popular platforms using these commands:

➤ <b>/fb [Video URL]</b> - Download a Facebook video.
- <i>Example:</i> /fb https://facebook.com/video/example

➤ <b>/pn [Video URL]</b> - Download a Pinterest video or image.
- <i>Example:</i> /pn https://pinterest.com/pin/example

➤ <b>/ig [URL]</b> - Download Instagram Reels & Posts.
- <i>Example:</i> /ig https://instagram.com/p/example

➤ <b>/x [Video URL]</b> - Download a Twitter/X video.
- <i>Example:</i> /x https://x.com/elonmusk/status/example

➤ <b>/tik [Video URL]</b> - Download a TikTok video.
- <i>Example:</i> /tik https://tiktok.com/@user/video/example

➤ <b>/tdl [Video URL]</b> - Download a Threads video.
- <i>Example:</i> /tdl https://www.threads.net/@user/post/example

➤ <b>/sp [Track URL]</b> - Download a Spotify track.
- <i>Example:</i> /sp https://open.spotify.com/track/example

➤ <b>/yt [Video URL]</b> - Download a YouTube video.
- <i>Example:</i> /yt https://youtube.com/watch?v=example

➤ <b>/song [Video URL]</b> - Download a YouTube video as an MP3 file.
- <i>Example:</i> /song https://youtube.com/watch?v=example

<b>NOTE:</b>
Provide a valid public URL for each platform to download successfully.
"""
    await callback.message.edit_text(text, reply_markup=get_downloader_menu_keyboard(), disable_web_page_preview=True)
    await callback.answer()