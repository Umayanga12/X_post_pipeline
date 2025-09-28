# x_client.py
# This file handles the initialization of the X (Twitter) client.

from typing import Optional
import tweepy
from config import logger, X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET


def init_twitter_client() -> Optional[tweepy.Client]:
    try:
        if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
            raise ValueError("Missing X API credentials")

        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET,
            wait_on_rate_limit=True,
        )
        logger.info("X client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to init X client: {e}")
        return None
