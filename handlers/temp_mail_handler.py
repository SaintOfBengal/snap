import aiohttp
import random
import string
import uuid
import re
from aiogram import types, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bs4 import BeautifulSoup

from keyboards.callbacks import TempMailCallback
from data_storage import temp_mail_data

API_BASE = "https://api.mail.tm"

def escape_html(text: str) -> str:
    """Escapes characters for HTML parsing."""
    return text.replace("&", "&").replace("<", "<").replace(">", ">")

# --- NEW: OTP and Link Extractor ---
def extract_otp_and_links(html_content: str) -> dict:
    """
    Scans HTML content to find OTPs (One-Time Passwords) and verification links.
    """
    if not html_content:
        return {'otps': [], 'links': []}

    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ')
    
    # --- Find OTPs ---
    # Common OTP patterns: 6-digit numbers, often near words like "code", "token", "password".
    otp_patterns = [
        r'(\b\d{6}\b)', # 6-digit number
        r'code is:\s*(\d+)',
        r'verification code:\s*(\d+)',
        r'security code:\s*(\w+)'
    ]
    otps = []
    for pattern in otp_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if match not in otps:
                otps.append(match)

    # --- Find Verification Links ---
    verification_links = []
    link_keywords = ['verify', 'confirm', 'activate', 'validate', 'complete']
    for a in soup.find_all('a', href=True):
        link_text = a.get_text().lower()
        # Check if any keyword is in the link's text
        if any(keyword in link_text for keyword in link_keywords):
            verification_links.append({'text': a.get_text(strip=True), 'href': a['href']})
    
    return {'otps': otps, 'links': verification_links}


# Handler for the /get_email command
async def get_temp_email(message: types.Message, bot: Bot):
    """
    Generates a new temporary email address from Mail.tm.
    """
    status_msg = await message.reply("Creating your temporary email... 📧")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/domains") as response:
                if not response.ok:
                    raise ConnectionError("Could not fetch domains.")
                domains = await response.json()
                domain = domains['hydra:member'][0]['domain']

            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            address = f"{username}@{domain}"

            account_payload = {"address": address, "password": password}
            async with session.post(f"{API_BASE}/accounts", json=account_payload) as response:
                if not response.status == 201:
                    raise ConnectionError(f"Could not create account.")

            token_payload = {"address": address, "password": password}
            async with session.post(f"{API_BASE}/token", json=token_payload) as response:
                if not response.ok:
                    raise ConnectionError("Could not get authentication token.")
                token_data = await response.json()
                token = token_data['token']

        session_id = str(uuid.uuid4())
        temp_mail_data[session_id] = {'token': token, 'address': address}

        builder = InlineKeyboardBuilder()
        check_inbox_callback = TempMailCallback(action="check", session_id=session_id).pack()
        builder.button(text="📬 Check Inbox", callback_data=check_inbox_callback)
        
        await status_msg.edit_text(
            f"✅ Here is your temporary email address:\n\n"
            f"<code>{address}</code>\n\n"
            f"Use this email for any sign-ups. Click the button below to check for new messages.",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ An error occurred:\n<code>{escape_html(str(e))}</code>")


# Handler for the "Check Inbox" button callback
async def check_temp_inbox(callback: types.CallbackQuery, bot: Bot):
    """
    Checks the inbox and extracts only OTPs and verification links.
    """
    await callback.answer("Checking inbox...")
    
    callback_data = TempMailCallback.unpack(callback.data)
    session_id = callback_data.session_id
    
    session_data = temp_mail_data.get(session_id)
    if not session_data:
        await callback.message.answer("❌ This email session has expired or is invalid. Please get a new one with /get_email.")
        return
        
    token = session_data['token']
    address = session_data['address']
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{API_BASE}/messages") as response:
                if not response.ok:
                    raise ConnectionError("Failed to fetch messages.")
                messages = await response.json()
        
            inbox = messages.get('hydra:member', [])
            if not inbox:
                await callback.answer("📭 Your inbox is empty.", show_alert=True)
                return
                
            await callback.message.answer(f"📬 Found {len(inbox)} message(s) for <b>{address}</b>:")

            for msg_preview in inbox:
                msg_id = msg_preview.get('id')
                if not msg_id:
                    continue
                
                # Fetch the full message content
                async with session.get(f"{API_BASE}/messages/{msg_id}") as msg_response:
                    if msg_response.ok:
                        full_msg = await msg_response.json()
                        html_body = (full_msg.get('html') or [''])[0]
                        # --- USE THE NEW EXTRACTOR ---
                        extracted_data = extract_otp_and_links(html_body)
                    else:
                        extracted_data = {'otps': [], 'links': []}
                
                from_email = escape_html(msg_preview['from']['address'])
                subject = escape_html(msg_preview.get('subject', 'N/A'))
                
                response_text = (
                    f"<b>From:</b> {from_email}\n"
                    f"<b>Subject:</b> {subject}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                )

                # --- Format the extracted data ---
                if not extracted_data['otps'] and not extracted_data['links']:
                    response_text += "<i>No specific OTP or verification link found. Check the full email manually if needed.</i>"
                else:
                    if extracted_data['otps']:
                        response_text += "🔑 <b>OTP/Code Found:</b>\n"
                        for otp in extracted_data['otps']:
                            response_text += f"<code>{otp}</code>\n"
                        response_text += "\n"

                    if extracted_data['links']:
                        response_text += "🔗 <b>Verification Link(s) Found:</b>\n"
                        for link in extracted_data['links']:
                            response_text += f'➤ <a href="{link["href"]}">{link["text"]}</a>\n'

                await callback.message.answer(response_text, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        await callback.message.answer(f"❌ An error occurred while checking the inbox:\n<code>{escape_html(str(e))}</code>")