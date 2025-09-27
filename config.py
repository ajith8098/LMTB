import os

# Get from environment variables
API_ID = os.getenv("23990433")
API_HASH = os.getenv("e6c4b6ee1933711bc4da9d7d17e1eb20")
BOT_TOKEN = os.getenv("7972560151:AAHlUN7BOsfPwu-LFUpuAV0YLqyGdkEXsrU")
MEGA_EMAIL = os.getenv("youtu0323@gmail.com")
MEGA_PASSWORD = os.getenv("12345678Sa@#$")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "/data/files")

# Convert API_ID to int safely
try:
    API_ID = int(API_ID) if API_ID else None
except (TypeError, ValueError):
    API_ID = None

# Validate required variables
if not API_ID:
    raise ValueError("API_ID is required and must be a number")
if not API_HASH:
    raise ValueError("API_HASH is required")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required")
