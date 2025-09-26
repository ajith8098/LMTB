import asyncio, os, time, pathlib, tempfile
from pyrogram import Client, filters
from pyrogram.types import Message
import config
from pymega import Mega
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pyrogram client (session name auto-created)
app = Client(
    "mega_link_downloader_bot",
    api_id=int(config.API_ID),
    api_hash=str(config.API_HASH),
    bot_token=str(config.BOT_TOKEN),
    workdir="."
)

# ThreadPool for blocking downloads (mega.py is blocking)
executor = ThreadPoolExecutor(max_workers=3)

def human_size(n):
    # simple human readable
    for unit in ['B','KB','MB','GB','TB']:
        if n < 1024.0:
            return f"{n:.2f}{unit}"
        n /= 1024.0
    return f"{n:.2f}PB"

async def progress_for_pyrogram(current, total, message: Message, start_time):
    now = time.time()
    diff = now - start_time
    if diff == 0:
        diff = 0.0001
    speed = current / diff
    percent = (current / total) * 100 if total else 0
    text = "Transferred: {:.2f}%\n{}/{}\nSpeed: {}/s\nElapsed: {:.1f}s".format(
        percent, human_size(current), human_size(total), human_size(speed), diff
    )
    try:
        await message.edit(text)
    except Exception:
        pass

def download_mega_link(link, dest_folder, email=None, password=None):
    """
    Blocking function run in ThreadPoolExecutor.
    Uses mega.py to download the file and returns the path to the downloaded file.
    """
    mega = Mega()
    if email and password:
        m = mega.login(email, password)
    else:
        m = mega.login()  # anonymous login for public links
    # mega.py provides download_url() that returns the downloaded path
    path = m.download_url(link, dest_folder)
    return path

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply_text("Hi! Send me a MEGA link (public or private). Use /download <link> to start.")

@app.on_message(filters.command("download") & filters.private)
async def download_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /download <mega_link>")
        return
    link = message.command[1].strip()
    await _handle_mega_link(client, message, link)

@app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?mega(\.co|\.nz)"))
async def inline_link_handler(client: Client, message: Message):
    # Extract first mega link from message text
    text = message.text or message.caption or ""
    # crude extraction
    for part in text.split():
        if "mega" in part:
            await _handle_mega_link(client, message, part)
            return
    await message.reply_text("No valid MEGA link found.")

async def _handle_mega_link(client: Client, message: Message, link: str):
    status = await message.reply_text("Starting download...")
    dest = config.DOWNLOAD_DIR if hasattr(config, 'DOWNLOAD_DIR') else '/tmp'
    os.makedirs(dest, exist_ok=True)
    # Run blocking download in threadpool
    loop = asyncio.get_event_loop()
    start = time.time()
    try:
        downloaded_path = await loop.run_in_executor(
            executor, download_mega_link, link, dest, getattr(config, 'MEGA_EMAIL', ''), getattr(config, 'MEGA_PASSWORD', '')
        )
    except Exception as e:
        await status.edit(f"Download failed: {e}")
        return
    if not downloaded_path or not os.path.exists(downloaded_path):
        await status.edit("Download failed or returned invalid path.")
        return
    fname = os.path.basename(downloaded_path)
    filesize = os.path.getsize(downloaded_path)
    await status.edit(f"Downloaded {fname} ({human_size(filesize)}). Uploading to Telegram...")
    start_upload = time.time()
    # send file with progress callback (pyrogram supports 'progress' and 'progress_args')
    try:
        await client.send_document(
            chat_id=message.chat.id,
            document=downloaded_path,
            caption=f"{fname} ({human_size(filesize)})",
            progress=progress_for_pyrogram,
            progress_args=(status, start_upload)
        )
    except Exception as e:
        await status.edit(f"Upload failed: {e}")
        return
    await status.delete()
    # Clean up downloaded file

if __name__ == "__main__":
    print("Bot is starting...")
    app.run()


from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn

web = FastAPI()

@web.get("/files/{filename}")
async def get_file(filename: str):
    filepath = os.path.join(config.DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename)
    return {"error": "File not found"}

if __name__ == "__main__":
    import threading
    def run_web():
        uvicorn.run(web, host="0.0.0.0", port=10000)

    threading.Thread(target=run_web, daemon=True).start()
    app.run()
