import asyncio, os, time, pathlib, tempfile
from pyrogram import Client, filters
from pyrogram.types import Message
import config
from concurrent.futures import ThreadPoolExecutor
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client(
    "mega_link_downloader_bot",
    api_id=int(config.API_ID),
    api_hash=str(config.API_HASH),
    bot_token=str(config.BOT_TOKEN),
    workdir="."
)

executor = ThreadPoolExecutor(max_workers=3)

def human_size(n):
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

def download_with_megatools(link, dest_folder, email=None, password=None):
    """Download using megatools command-line utility"""
    try:
        # Install megatools if not present
        try:
            subprocess.run(['megatools', '--version'], capture_output=True, check=True)
        except:
            logger.info("Installing megatools...")
            subprocess.run(['apt-get', 'update'], check=True)
            subprocess.run(['apt-get', 'install', '-y', 'megatools'], check=True)
        
        # Create config for megatools if credentials provided
        if email and password:
            config_content = f"[Login]\nUsername = {email}\nPassword = {password}\n"
            config_path = os.path.expanduser("~/.megatoolsrc")
            with open(config_path, 'w') as f:
                f.write(config_content)
            os.chmod(config_path, 0o600)
        
        # Download the file
        cmd = ['megatools', 'dl', link, '--path', dest_folder]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=dest_folder)
        
        if result.returncode == 0:
            # Find the downloaded file
            for file in os.listdir(dest_folder):
                filepath = os.path.join(dest_folder, file)
                if os.path.isfile(filepath) and not file.startswith('.'):
                    return filepath
        logger.error(f"Megatools failed: {result.stderr}")
        return None
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None

# ... keep the rest of your handlers exactly as they were
# Just replace the download_mega_link function call with download_with_megatools
