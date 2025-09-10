import os
import asyncio
import aiohttp
from aiogram import types, Bot

def escape_html(text: str) -> str:
    """A simple function to escape basic HTML characters."""
    if not isinstance(text, str):
        return ""
    return text.replace("&", "&").replace("<", "<").replace(">", ">")

async def handle_imagine(message: types.Message, bot: Bot):
    """
    Handles the /imagine command by communicating directly with the Stable Horde API.
    """
    prompt = message.text.replace("/imagine", "").strip()

    if not prompt:
        await message.reply("Please provide a prompt after the command.\n<b>Example:</b> /imagine a beautiful castle in the clouds")
        return

    status_msg = await message.reply(f"🎨 Sending prompt to the horde...\n<i>\"{escape_html(prompt)}\"</i>\n\nYour request is in the queue. This may take a few minutes.")

    api_key = os.getenv("STABLE_HORDE_API_KEY", "0000000000")
    api_headers = {"apikey": api_key, "Client-Agent": "AIO_Bot:1.0:github.com/gemini/bot"}
    
    payload = {
        "prompt": prompt,
        "params": {"n": 1, "width": 512, "height": 512},
        "models": ["Anything V5"]
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Submit the generation request
            async with session.post('https://stablehorde.net/api/v2/generate/async', headers=api_headers, json=payload) as response:
                if not response.ok:
                    raise Exception(f"Failed to submit request: {await response.text()}")
                job_data = await response.json()
                job_id = job_data.get('id')

            if not job_id:
                raise Exception("Could not get a Job ID from the Horde.")

            # 2. Poll for the result
            while True:
                await asyncio.sleep(10)
                check_url = f'https://stablehorde.net/api/v2/generate/check/{job_id}'
                async with session.get(check_url) as response:
                    status_data = await response.json()
                    if status_data.get('done'):
                        break
            
            # 3. Retrieve the final image
            status_url = f'https://stablehorde.net/api/v2/generate/status/{job_id}'
            async with session.get(status_url) as response:
                final_data = await response.json()

            if final_data.get('generations'):
                image_url = final_data['generations'][0]['img']
                
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=image_url,
                    caption=f"✅ Here is your generated image for:\n<i>\"{escape_html(prompt)}\"</i>"
                )
                await status_msg.delete()
            else:
                error_message = final_data.get('faulted', 'Job faulted or timed out.')
                await status_msg.edit_text(f"❌ The horde could not generate an image. Reason: {escape_html(error_message)}")

    except Exception as e:
        await status_msg.edit_text(f"❌ An error occurred: {escape_html(str(e))}")