from aiogram import Dispatcher, Bot, F
from aiogram.filters import Command, CommandStart
from functools import partial

# Callback Factories
from keyboards.callbacks import YouTubeCallback, TempMailCallback

# Menu Handlers
from .menu_handlers import (
    start_handler, main_menu_handler, menu_page_handler,
    about_me_handler, policy_terms_handler, close_menu_handler,
    downloaders_menu_handler
)
# Social Media Downloaders
from .youtube import handle_youtube, youtube_quality_callback
from .youtube_audio import handle_youtube_audio
from .facebook import handle_facebook
from .tiktok import handle_tiktok
from .instagram import handle_instagram
from .twitter import handle_twitter
from .pinterest import handle_pinterest
from .threads import handle_threads
from .spotify import handle_spotify

# Utility Handlers
from .qr_handler import handle_qr
from .temp_mail_handler import get_temp_email, check_temp_inbox
from .paste_handler import handle_paste
from .ai_handler import handle_imagine


def register_all_handlers(dp: Dispatcher, bot: Bot):

    # Register Menu Handlers
    dp.message.register(start_handler, CommandStart())
    dp.callback_query.register(main_menu_handler, F.data == "main_menu")
    dp.callback_query.register(menu_page_handler, F.data.startswith("menu_page:"))
    dp.callback_query.register(about_me_handler, F.data == "about_me")
    dp.callback_query.register(policy_terms_handler, F.data == "policy_terms")
    dp.callback_query.register(close_menu_handler, F.data == "close_menu")
    dp.callback_query.register(downloaders_menu_handler, F.data == "downloaders_menu")

    # Register Downloader Handlers
    dp.message.register(partial(handle_facebook, bot=bot), Command("fb"))
    dp.message.register(partial(handle_pinterest, bot=bot), Command("pn"))
    dp.message.register(partial(handle_instagram, bot=bot), Command("ig"))
    dp.message.register(partial(handle_twitter, bot=bot), Command("x"))
    dp.message.register(partial(handle_tiktok, bot=bot), Command("tik"))
    dp.message.register(partial(handle_threads, bot=bot), Command("tdl"))
    dp.message.register(partial(handle_spotify, bot=bot), Command("sp"))
    dp.message.register(partial(handle_youtube, bot=bot), Command("yt"))
    dp.message.register(partial(handle_youtube_audio, bot=bot), Command("song"))

    # Register Utility Handlers
    dp.message.register(partial(handle_qr, bot=bot), Command("qr"))
    dp.message.register(partial(get_temp_email, bot=bot), Command("get_email"))
    dp.message.register(partial(handle_paste, bot=bot), Command("paste"))
    dp.message.register(partial(handle_imagine, bot=bot), Command("imagine"))

    # Register Callback Handlers
    dp.callback_query.register(partial(youtube_quality_callback, bot=bot), YouTubeCallback.filter())
    dp.callback_query.register(partial(check_temp_inbox, bot=bot), TempMailCallback.filter(F.action == "check"))