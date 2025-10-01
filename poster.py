# This file handles posting to X, including media upload.

from typing import Dict, Optional
import tweepy
from config import logger
from x import init_twitter_client


def post_to_x(post: Dict) -> bool:
    client = init_twitter_client()
    if not client:
        logger.error("No X client available")
        return False
    try:
        media_ids = None
        if post["image_path"]:
            media = client.media_upload(filename=post["image_path"])
            media_ids = [media.media_id_string]

        response = client.create_tweet(text=post["text"], media_ids=media_ids)
        tweet_id = response.data.get("id")
        logger.info(f"Posted tweet ID: {tweet_id}")
        return True
    except tweepy.Forbidden as e:
        logger.error(f"403 Forbidden: {e}. Check API permissions")
    except tweepy.TooManyRequests:
        logger.warning("Rate limit hit; retry later")
    except Exception as e:
        logger.error(f"Post failed: {e}")
    return False
