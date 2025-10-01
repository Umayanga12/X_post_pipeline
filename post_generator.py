import random

from config import KEYWORDS
from imagepicker import pick_image
import urllib.request


def generate_post(article: dict) -> dict:
    # Base hashtags
    base_tags = "#Crypto #Web3 #NFTs #Blockchain #Ethereum #Bitcoin"

    # Emoji sets for visual appeal
    emojis = {
        "crypto": ["💸", "📈", "🚀"],
        "nft": ["🖼️", "🎨", "🪙"],
        "web3": ["🌐", "🔗", "🛠️"],
        "blockchain": ["⛓️", "🔒", "📡"],
        "ethereum": ["Ξ", "🧠", "💻"],
        "bitcoin": ["₿", "💰", "🔥"],
    }

    # Dynamic post templates
    templates = [
        "{emoji} {title}\n\n{snippet}... {cta}\n\n{link} {tags}",
        "{emoji} 🚨 Breaking: {title}\n\n{snippet}... {cta}\n\n{link} {tags}",
        "{emoji} 🔥 Hot Topic: {title}\n\n{snippet}... {cta}\n\n{link} {tags}",
        "{emoji} Curious about {keyword}? {title}\n\n{snippet}... {cta}\n\n{link} {tags}",
        "{emoji} Big news in {keyword}! {title}\n\n{snippet}... {cta}\n\n{link} {tags}",
    ]

    # CTAs to encourage engagement
    ctas = [
        "Read more! 👇",
        "What do you think? 🤔",
        "Dive in! 🔍",
        "Check it out! 🚀",
        "Join the conversation! 💬",
    ]

    # Extract snippet and ensure it's concise
    snippet = article.get("snippet") or article.get("summary", "")
    snippet = (
        snippet[:150] + "..." if len(snippet) > 150 else snippet
    )  # Shorten for engagement

    # Pick relevant keywords and emojis
    post_keywords = [
        kw
        for kw in KEYWORDS
        if kw.lower() in article.get("title", "").lower()
        or kw.lower() in snippet.lower()
    ]
    selected_keyword = (
        random.choice(post_keywords) if post_keywords else random.choice(KEYWORDS)
    )
    selected_emoji = random.choice(emojis.get(selected_keyword.lower(), ["🌟"]))

    # Add dynamic hashtags based on post_keywords
    dynamic_tags = ""
    if post_keywords:
        # Remove duplicates and keep only alphanumeric for hashtags
        unique_keywords = []
        for kw in post_keywords:
            tag = "#" + "".join(c for c in kw if c.isalnum())
            if tag.lower() not in [t.lower() for t in unique_keywords]:
                unique_keywords.append(tag)
        dynamic_tags = " " + " ".join(unique_keywords)
    else:
        dynamic_tags = ""

    # Combine base tags and dynamic tags
    all_tags = base_tags + dynamic_tags

    # Choose a random template and CTA
    template = random.choice(templates)
    cta = random.choice(ctas)

    articleLink = None
    try:
        statCode = urllib.request.urlopen(article.get("link", "")).getcode()
        if statCode == 200:
            articleLink = article.get("link", "")
    except Exception:
        articleLink = None

    # Generate post text
    post_text = template.format(
        emoji=selected_emoji,
        title=article.get("title", ""),
        snippet=snippet,
        cta=cta,
        link=articleLink,
        tags=all_tags,
        keyword=selected_keyword.capitalize(),
    )

    # Ensure post is within X's 280-character limit
    post_text = post_text[:277] + "..." if len(post_text) > 280 else post_text

    # Pick image based on keywords
    image_path = pick_image(post_keywords) if post_keywords else None

    return {
        "text": post_text,
        "image_path": image_path,
        "url": article.get("link", ""),
        "full_text": article.get("full_text", snippet),
    }
