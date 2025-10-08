from typing import Dict, Optional
import tweepy
from config import (
    logger,
    X_API_KEY,
    X_API_SECRET,
    X_ACCESS_TOKEN,
    X_ACCESS_SECRET,
)
from x import init_twitter_client


def post_to_x(post: Dict) -> bool:
    """Post a tweet with optional image."""
    client = init_twitter_client()
    if not client:
        logger.error("❌ No X client available")
        return False

    try:
        media_ids = None

        # # --- Use Tweepy v1.1 API for media upload ---
        if post.get("image_path"):
            try:
                auth = tweepy.OAuth1UserHandler(
                    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
                )
                api = tweepy.API(auth)
                media = api.media_upload(filename=post["image_path"])
                media_ids = [media.media_id_string]
                logger.info(f"📸 Uploaded media ID: {media.media_id_string}")
            except Exception as e:
                logger.warning(f"⚠️ Image upload failed: {e}. Skipping image.")

        # --- Create tweet via v2 client ---
        # response = client.create_tweet(text=post["text"], media_ids=media_ids)
        response = client.create_tweet(text=post["text"])
        tweet_id = response.data.get("id")
        logger.info(f"✅ Posted tweet ID: {tweet_id}")
        return True

    except tweepy.Forbidden as e:
        logger.error(f"🚫 403 Forbidden: {e}. Check API permissions")
    except tweepy.TooManyRequests:
        logger.warning("⚠️ Rate limit hit; retry later")
    except Exception as e:
        logger.error(f"❌ Post failed: {e}")

    return False
