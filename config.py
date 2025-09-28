import os
from dotenv import load_dotenv

load_dotenv()

# Logging configuration
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

POSTED_FILE = os.getenv("POSTED_FILE", "posted.json")
IMAGE_FOLDER = os.getenv(
    "IMAGE_FOLDER", "images"
)  # Base folder for images, with subfolders like 'crypto', 'nft', etc.

# RSS feeds and scrape URLs
RSS_URLS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://beincrypto.com/feed/",
    "https://www.theblock.co/feed",
    "https://u.today/rss",
    "https://nftlately.com/feed/",
    "https://nftplazas.com/feed/",
    "https://nftnow.com/feed/",
    "https://nftcalendar.io/feed/",
    "https://decrypt.co/feed",
    "https://coingape.com/feed/",
    "https://ambcrypto.com/feed/",
]

SCRAPE_BASE_URLS = [
    "https://cointelegraph.com/",
    "https://www.coindesk.com/",
    "https://beincrypto.com/",
    "https://www.theblock.co/",
    "https://u.today/",
    "https://nftlately.com/",
    "https://nftplazas.com/",
    "https://nftnow.com/",
    "https://nftcalendar.io/",
    "https://decrypt.co/",
    "https://coingape.com/",
    "https://ambcrypto.com/",
]

KEYWORDS = ["crypto", "nft", "web3", "blockchain", "ethereum", "bitcoin"]

# Queue settings
POST_QUEUE_SIZE = 100  # Max items in queue
POST_INTERVAL_SECONDS = 3600  # Post every hour (3600 seconds)
DUPLICATE_THRESHOLD = 0.85  # Cosine similarity threshold for duplicates
HISTORY_RETENTION_DAYS = 30  # Keep history for 30 days
