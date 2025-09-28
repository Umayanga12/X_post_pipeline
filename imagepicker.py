import os
import random


def pick_image(keywords):
    image_folder = f"image/{keywords}"
    images = os.listdir(image_folder)
    # Simple keyword match in filename
    matches = [
        img for img in images if any(kw.lower() in img.lower() for kw in keywords)
    ]
    if matches:
        return os.path.join(image_folder, random.choice(matches))
    # Fallback: random image
    if images:
        return os.path.join(image_folder, random.choice(images))
    return None


print(pick_image("crypto"))
