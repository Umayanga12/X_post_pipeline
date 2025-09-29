import json
import os
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List
from config import logger, POSTED_FILE, DUPLICATE_THRESHOLD, HISTORY_RETENTION_DAYS

vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")

# Initialize posted_data with default structure
posted_data: Dict[str, List] = {"urls": [], "timestamps": [], "texts": []}


def load_posted() -> Dict[str, List]:
    global posted_data
    default_data = {"urls": [], "timestamps": [], "texts": []}

    if not os.path.exists(POSTED_FILE):
        logger.info(f"No posted file found at {POSTED_FILE}. Initializing new data.")
        posted_data = default_data
        with open(POSTED_FILE, "w") as f:
            json.dump(posted_data, f, indent=2)
        return posted_data

    try:
        with open(POSTED_FILE, "r") as f:
            loaded_data = json.load(f)
            # Ensure all required keys exist
            for key in default_data:
                if key not in loaded_data:
                    logger.warning(
                        f"Missing key '{key}' in {POSTED_FILE}. Adding default."
                    )
                    loaded_data[key] = default_data[key]
            posted_data = loaded_data
            logger.info("Loaded posted data")
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load {POSTED_FILE}: {e}. Initializing default data.")
        posted_data = default_data
        with open(POSTED_FILE, "w") as f:
            json.dump(posted_data, f, indent=2)

    return posted_data


def is_duplicate(full_text: str) -> bool:
    load_posted()
    # Check if texts exist and are non-empty
    if not posted_data.get("texts"):
        return False
    try:
        vectors = vectorizer.fit_transform([full_text] + posted_data["texts"])
        sims = cosine_similarity(vectors[0:1], vectors[1:])[0]
        return any(s > DUPLICATE_THRESHOLD for s in sims)
    except Exception as e:
        logger.error(f"Error in duplicate check: {e}")
        return False


def save_posted(url: str, full_text: str):
    load_posted()
    cutoff = (datetime.now() - timedelta(days=HISTORY_RETENTION_DAYS)).timestamp()

    # Clean old records
    filtered = [
        (u, t, txt)
        for u, t, txt in zip(
            posted_data["urls"], posted_data["timestamps"], posted_data["texts"]
        )
        if t > cutoff
    ]
    if filtered:
        posted_data["urls"], posted_data["timestamps"], posted_data["texts"] = zip(
            *filtered
        )
    else:
        posted_data["urls"], posted_data["timestamps"], posted_data["texts"] = (
            [],
            [],
            [],
        )

    posted_data["urls"].append(url)
    posted_data["timestamps"].append(datetime.now().timestamp())
    posted_data["texts"].append(full_text[:2000])  # Truncate for storage

    try:
        with open(POSTED_FILE, "w") as f:
            json.dump(posted_data, f, indent=2)
        logger.info(f"Saved posted article: {url}")
    except Exception as e:
        logger.error(f"Failed to save posted data: {e}")
