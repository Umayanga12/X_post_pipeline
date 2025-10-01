import feedparser
import requests
from bs4 import BeautifulSoup
from newspaper import Article, Config
import re
from typing import List, Dict
from config import logger, RSS_URLS, SCRAPE_BASE_URLS, KEYWORDS


def fetch_from_rss(rss_urls: List[str]) -> List[Dict]:
    logger.info("fetching rss feeds...")
    articles = []
    for url in rss_urls:
        print(f"Fetching RSS URL: {url}")
        try:
            feed = feedparser.parse(url)
            print(f"Parsed feed: {url}, found {len(feed.entries)} entries")
            for entry in feed.entries:
                print(f"Checking entry: {getattr(entry, 'title', 'NO TITLE')}")
                if any(
                    kw.lower() in entry.title.lower()
                    or kw.lower() in entry.summary.lower()
                    for kw in KEYWORDS
                ):
                    print(f"Matched entry with keywords: {entry.title}")
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
            print(f"Exception while fetching RSS from {url}: {e}")
    print(f"Total articles fetched from RSS: {len(articles)}")
    return articles


def scrape_articles(base_urls: List[str]) -> List[Dict]:
    logger.info("fetching from base urls....")
    articles = []
    for base_url in base_urls:
        print(f"Scraping base URL: {base_url}")
        try:
            response = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"})
            print(f"HTTP GET {base_url} status: {response.status_code}")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            links = [
                a["href"]
                for a in soup.find_all("a", href=True)
                if any(kw.lower() in a["href"].lower() for kw in KEYWORDS)
            ]
            print(f"Found {len(links)} links matching keywords at {base_url}")
            for link in set(links):  # Dedup links
                print(f"Processing link: {link}")
                if not link.startswith("http"):
                    link = base_url.rstrip("/") + "/" + link.lstrip("/")
                    print(f"Normalized link to: {link}")
                article_data = extract_article_content(link)
                print(
                    f"Extracted article_data for {link}: {article_data.get('success')}"
                )
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
                else:
                    print(
                        f"Failed to extract article content for {link}: {article_data.get('error')}"
                    )
            logger.info(f"Scraped {len(links)} potential articles from {base_url}")
        except Exception as e:
            logger.error(f"Failed to scrape {base_url}: {e}")
            print(f"Exception while scraping {base_url}: {e}")
    print(f"Total articles scraped: {len(articles)}")
    return articles


def extract_article_content(url: str) -> Dict:
    print(f"Extracting article content from: {url}")
    try:
        config = Config()
        config.browser_user_agent = "Mozilla/5.0"
        config.request_timeout = 10

        article = Article(url, config=config)
        print(f"Downloading article: {url}")
        article.download()
        print(f"Parsing article: {url}")
        article.parse()
        print(f"Running NLP on article: {url}")
        article.nlp()

        clean_text = re.sub(r"\s+", " ", article.text).strip()
        print(f"Extracted text length: {len(clean_text)} for {url}")

        return {
            "title": article.title,
            "text": clean_text,
            "summary": article.summary,
            "publish_date": str(article.publish_date) if article.publish_date else None,
            "url": url,
            "success": True,
        }
    except Exception as e:
        print(f"Exception in extract_article_content for {url}: {e}")
        return {"success": False, "error": str(e), "url": url}
