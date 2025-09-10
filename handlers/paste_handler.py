from aiogram import types, Bot
from telegraph.aio import Telegraph

# Initialize the Telegraph client
telegraph = Telegraph()

# A flag to ensure we only create the Telegraph account once per bot run
account_created = False

async def create_telegraph_account(bot_username: str):
    """Creates a new Telegraph account for the bot if one doesn't exist."""
    global account_created
    if not account_created:
        await telegraph.create_account(
            short_name='AIO Bot', # You can change this
            author_name=bot_username,
            author_url=f'https://t.me/{bot_username}'
        )
        account_created = True

async def handle_paste(message: types.Message, bot: Bot):
    """
    Handles the /paste command to upload text to Telegraph.
    """
    # Create an account for our bot on the first run
    # We pass the bot's username to be used as the author name
    me = await bot.get_me()
    await create_telegraph_account(me.username)

    # Determine which text to use
    text_to_paste = ""
    if message.reply_to_message and message.reply_to_message.text:
        text_to_paste = message.reply_to_message.text
    elif len(message.text.split(maxsplit=1)) > 1:
        text_to_paste = message.text.split(maxsplit=1)[1]
    else:
        await message.reply(
            "<b>Usage:</b>\n"
            "➤ Reply to a message with <code>/paste</code>\n"
            "➤ Or use <code>/paste your long text here...</code>"
        )
        return

    status_msg = await message.reply("Pasting to Telegraph... 📜")

    try:
        html_content = f"<pre>{text_to_paste}</pre>"
        
        response = await telegraph.create_page(
            title='A Paste from AIO Bot', # You can change this title
            html_content=html_content
        )
        
        page_url = response['url']
        await status_msg.edit_text(
            f"✅ Text has been pasted successfully!\n\n"
            f"🔗 <b>Link:</b> {page_url}",
            disable_web_page_preview=True
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ An error occurred: {e}")