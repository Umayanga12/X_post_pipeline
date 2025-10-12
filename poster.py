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
    print("DEBUG: Entered post_to_x function")
    print(f"DEBUG: post argument: {post}")
    client = init_twitter_client()
    print(f"DEBUG: Twitter client initialized: {client}")
    if not client:
        logger.error("❌ No X client available")
        print("DEBUG: No X client available, returning False")
        return False

    try:
        media_ids = None
        print("DEBUG: media_ids initialized to None")

        # --- Use Tweepy v1.1 API for media upload ---
        if post.get("image_path"):
            print(f"DEBUG: image_path found in post: {post.get('image_path')}")
            try:
                print("DEBUG: Setting up Tweepy OAuth1UserHandler")
                auth = tweepy.OAuth1UserHandler(
                    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
                )
                api = tweepy.API(auth)
                print(f"DEBUG: Tweepy API object created: {api}")
                media = api.media_upload(filename=post["image_path"])
                print(f"DEBUG: Media uploaded: {media}")
                media_ids = [media.media_id_string]
                print(f"DEBUG: media_ids set to: {media_ids}")
                logger.info(f"📸 Uploaded media ID: {media.media_id_string}")
            except Exception as e:
                logger.warning(f"⚠️ Image upload failed: {e}. Skipping image.")
                print(f"DEBUG: Exception during image upload: {e}")

        # --- Create tweet via v2 client ---
        if media_ids:
            print(
                f"DEBUG: Creating tweet with text: {post['text']} and media_ids: {media_ids}"
            )
            response = client.create_tweet(text=post["text"], media_ids=media_ids)
            print(response)
        else:
            print(f"DEBUG: Creating tweet with text: {post['text']}")
            response = client.create_tweet(text=post["text"])
        print(f"DEBUG: Tweet creation response: {response}")
        tweet_id = response.data.get("id")
        print(f"DEBUG: Tweet ID from response: {tweet_id}")
        logger.info(f"✅ Posted tweet ID: {tweet_id}")
        return True

    except tweepy.Forbidden as e:
        logger.error(f"🚫 403 Forbidden: {e}. Check API permissions")
        print(f"DEBUG: tweepy.Forbidden exception: {e}")
    except tweepy.TooManyRequests:
        logger.warning("⚠️ Rate limit hit; retry later")
        print("DEBUG: tweepy.TooManyRequests exception")
    except Exception as e:
        logger.error(f"❌ Post failed: {e}")
        print(f"DEBUG: General exception: {e}")

    print("DEBUG: Returning False from post_to_x")
    return False
