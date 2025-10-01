import os
import random
from config import IMAGE_FOLDER, KEYWORDS


def pick_image(keywords: list[str]) -> str | None:
    for kw in keywords:
        image_subfolder = os.path.join(IMAGE_FOLDER, kw.lower())
        if os.path.exists(image_subfolder):
            images = [
                f
                for f in os.listdir(image_subfolder)
                if os.path.isfile(os.path.join(image_subfolder, f))
            ]
            if images:
                return os.path.join(image_subfolder, random.choice(images))
    # Fallback to random keyword
    random_kw = random.choice(KEYWORDS)
    image_subfolder = os.path.join(IMAGE_FOLDER, random_kw.lower())
    if os.path.exists(image_subfolder):
        images = [
            f
            for f in os.listdir(image_subfolder)
            if os.path.isfile(os.path.join(image_subfolder, f))
        ]
        if images:
            return os.path.join(image_subfolder, random.choice(images))
    return None
