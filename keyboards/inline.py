from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

MENU_BUTTONS = [
    ("AI Tools", "ai_tools"), ("CC Tools", "cc_tools"),
    ("Crypto", "crypto"), ("Converter", "converter"),
    ("Coupons", "coupons"), ("Decoders", "decoders"),
    ("Downloaders", "downloaders_menu"), ("Domain Check", "domain_check"),
    ("Education Utils", "education_utils"), ("Editing Utils", "editing_utils"),
]

def get_start_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Main Menu", callback_data="main_menu")],
        [
            InlineKeyboardButton(text="About Me", callback_data="about_me"),
            InlineKeyboardButton(text="Policy & Terms", callback_data="policy_terms")
        ]
    ])
    return keyboard

def get_main_menu_keyboard(page: int = 0):
    buttons_per_page = 10
    start = page * buttons_per_page
    end = start + buttons_per_page
    
    keyboard_buttons = []
    chunk = MENU_BUTTONS[start:end]
    for i in range(0, len(chunk), 2):
        row = [InlineKeyboardButton(text=text, callback_data=cbd) for text, cbd in chunk[i:i+2]]
        keyboard_buttons.append(row)
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Back", callback_data=f"menu_page:{page-1}"))
    if end < len(MENU_BUTTONS):
        nav_row.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"menu_page:{page+1}"))
    
    keyboard_buttons.append(nav_row)
    keyboard_buttons.append([InlineKeyboardButton(text="Close ❌", callback_data="close_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

def get_downloader_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Main Menu", callback_data="main_menu")]
    ])
    return keyboard