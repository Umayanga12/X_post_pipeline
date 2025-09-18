import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser
import tweepy
from dotenv import load_dotenv
import hashlib
from urllib.parse import urlparse, urlunparse

# Config: Secure env vars and logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CryptoPoster:
    def __init__(self):
        self.client_id = os.getenv('X_CLIENT_ID')
        self.client_secret = os.getenv('X_CLIENT_SECRET')
        self.refresh_token = os.getenv('X_REFRESH_TOKEN')
        self.posted_file = os.getenv('POSTED_FILE', 'posted.json')
        self.client = self._init_twitter_client()
        self.posted_data = self._load_posted()

    def _init_twitter_client(self) -> Optional[tweepy.Client]:
        """Initialize X client with OAuth 2.0."""
        try:
            auth = tweepy.OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri="http://localhost:3000",
                scope=["tweet.read", "tweet.write", "users.read"],
                client_secret=self.client_secret
            )
            auth.set_refresh_token(self.refresh_token)
            access_token = auth.refresh_token()
            return tweepy.Client(
                access_token=access_token["access_token"],
                wait_on_rate_limit=True
            )
        except Exception as e:
            logger.error(f"Failed to init X client: {e}")
            return None

    def _normalize_url(self, url: str) -> str:
        """Strip query params and fragments for consistent URL matching."""
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

    def _hash_content(self, title: str, snippet: str) -> str:
        """Create a unique hash for article title + snippet."""
        return hashlib.md5(f"{title}:{snippet}".encode()).hexdigest()

    def _load_posted(self) -> Dict:
        """Load posted data with error handling."""
        try:
            with open(self.posted_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    logger.warning("posted.json is empty; initializing new data")
                    return {"urls": [], "hashes": [], "timestamps": []}
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON format")
                return data
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Error loading posted data: {e}. Starting fresh.")
            return {"urls": [], "hashes": [], "timestamps": []}

    def _save_posted(self, url: str, content_hash: str):
        """Save URL, hash, and timestamp; prune old entries (>30 days)."""
        try:
            cutoff = (datetime.now() - timedelta(days=30)).timestamp()
            self.posted_data['urls'] = [
                u for u, t in zip(self.posted_data.get('urls', []), self.posted_data.get('timestamps', []))
                if t > cutoff
            ]
            self.posted_data['hashes'] = [
                h for h, t in zip(self.posted_data.get('hashes', []), self.posted_data.get('timestamps', []))
                if t > cutoff
            ]
            self.posted_data['timestamps'] = [t for t in self.posted_data.get('timestamps', []) if t > cutoff]

            self.posted_data.setdefault('urls', []).append(url)
            self.posted_data.setdefault('hashes', []).append(content_hash)
            self.posted_data.setdefault('timestamps', []).append(datetime.now().timestamp())

            with open(self.posted_file, 'w') as f:
                json.dump(self.posted_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save posted data: {e}")

    def fetch_news(self, rss_urls: List[str], max_age_hours: int = 24) -> List[Dict]:
        """Fetch articles, filter duplicates by URL and content hash."""
        articles = []
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        posted_urls = set(self.posted_data.get('urls', []))
        posted_hashes = set(self.posted_data.get('hashes', []))

        for url in rss_urls:
            try:
                feed = feedparser.parse(url, request_headers={'User-Agent': 'Mozilla/5.0'})
                for entry in feed.entries[:5]:
                    pub_date = datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else datetime.now()
                    if pub_date <= cutoff:
                        continue
                    norm_url = self._normalize_url(entry.link)
                    content_hash = self._hash_content(entry.title, entry.summary or '')
                    if norm_url not in posted_urls and content_hash not in posted_hashes:
                        articles.append({
                            'title': entry.title,
                            'link': entry.link,
                            'snippet': (entry.summary or '')[:100] + '...' if entry.summary else '',
                            'source': feed.feed.title,
                            'norm_url': norm_url,
                            'content_hash': content_hash
                        })
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
        logger.info(f"Fetched {len(articles)} new articles")
        return articles[:3]

    def generate_post(self, article: Dict) -> str:
        """Generate X post under 280 chars."""
        post = f"{article['title']}\n\n{article['snippet']}\n\n{article['link']} #Crypto #Web3 #NFTs"
        if len(post) > 280:
            post = post[:277] + '...'
        return post

    def post_to_x(self, post_text: str) -> bool:
        """Post with retry logic."""
        if not self.client:
            logger.error("No X client available")
            return False
        try:
            logger.debug(f"Attempting to post: {post_text}")
            response = self.client.create_tweet(text=post_text)
            logger.info(f"Posted tweet ID: {response.data['id']}")
            return True
        except tweepy.TooManyRequests:
            logger.warning("Rate limit hit; retry later")
            return False
        except tweepy.Forbidden as e:
            logger.error(f"403 Forbidden: {e}. Check OAuth 2.0 permissions and refresh token")
            return False
        except Exception as e:
            logger.error(f"Post failed: {e}")
            return False

    def run_pipeline(self, rss_urls: List[str]):
        """Main orchestrator."""
        articles = self.fetch_news(rss_urls)
        if not articles:
            logger.info("No new articles; skipping")
            return
        article = articles[0]
        post_text = self.generate_post(article)
        if self.post_to_x(post_text):
            self._save_posted(article['norm_url'], article['content_hash'])
        else:
            logger.error("Pipeline failed; manual check needed")

if __name__ == "__main__":
    rss_urls = [
        'https://cointelegraph.com/rss',
        'https://nftlately.com/feed/'
    ]
    poster = CryptoPoster()
    poster.run_pipeline(rss_urls)
