from aiogram.filters.callback_data import CallbackData

class YouTubeCallback(CallbackData, prefix="yt"):
    """
    CallbackData for YouTube quality selection.
    """
    video_id: str
    quality: str
    ext: str

# Replace the old TempMailCallback with this new one
class TempMailCallback(CallbackData, prefix="mail"):
    """
    CallbackData for the Temp Mail service.
    Fields:
    - action: The action to perform (e.g., 'check').
    - session_id: A unique ID to look up the session data from our storage.
    """
    action: str
    session_id: str