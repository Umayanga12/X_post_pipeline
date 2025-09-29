import feedparser
import requests
from bs4 import BeautifulSoup
from newspaper import Article, Config
import re
from typing import List, Dict
from config import logger, RSS_URLS, SCRAPE_BASE_URLS, KEYWORDS


def fetch_from_rss(rss_urls: List[str]) -> List[Dict]:
    articles = []
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if any(
                    kw.lower() in entry.title.lower()
                    or kw.lower() in entry.summary.lower()
                    for kw in KEYWORDS
                ):
                    articles.append(
                        {
                            "title": entry.title,
                            "snippet": entry.summary,
                            "link": entry.link,
                            "publish_date": entry.get("published"),
                        }
                    )
            logger.info(f"Fetched {len(feed.entries)} entries from {url}")
        except Exception as e:
            logger.error(f"Failed to fetch RSS from {url}: {e}")
    return articles


def scrape_articles(base_urls: List[str]) -> List[Dict]:
    articles = []
    for base_url in base_urls:
        try:
            response = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            links = [
                a["href"]
                for a in soup.find_all("a", href=True)
                if any(kw.lower() in a["href"].lower() for kw in KEYWORDS)
            ]
            for link in set(links):  # Dedup links
                if not link.startswith("http"):
                    link = base_url.rstrip("/") + "/" + link.lstrip("/")
                article_data = extract_article_content(link)
                if article_data["success"]:
                    articles.append(
                        {
                            "title": article_data["title"],
                            "snippet": article_data["summary"],
                            "link": link,
                            "publish_date": article_data["publish_date"],
                            "full_text": article_data["text"],
                        }
                    )
            logger.info(f"Scraped {len(links)} potential articles from {base_url}")
        except Exception as e:
            logger.error(f"Failed to scrape {base_url}: {e}")
    return articles


def extract_article_content(url: str) -> Dict:
    try:
        config = Config()
        config.browser_user_agent = "Mozilla/5.0"
        config.request_timeout = 10

        article = Article(url, config=config)
        article.download()
        article.parse()
        article.nlp()

        clean_text = re.sub(r"\s+", " ", article.text).strip()

        return {
            "title": article.title,
            "text": clean_text,
            "summary": article.summary,
            "publish_date": str(article.publish_date) if article.publish_date else None,
            "url": url,
            "success": True,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}
