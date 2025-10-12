import random
import urllib.request
from config import KEYWORDS
from imagepicker import pick_image


def generate_post(article: dict) -> dict:
    """Generate a varied, Twitter/X-friendly post from an article."""
    # Base hashtags (reduced to avoid spam flags)
    base_tags = "#Crypto #Blockchain"  # Keep minimal, relevant tags

    # Emoji sets for visual appeal
    emojis = {
        "crypto": ["💸", "📈", "🚀"],
        "nft": ["🖼️", "🎨", "🪙"],
        "web3": ["🌐", "🔗", "🛠️"],
        "blockchain": ["⛓️", "🔒", "📡"],
        "ethereum": ["Ξ", "🧠", "💻"],
        "bitcoin": ["₿", "💰", "🔥"],
    }

    # More varied post templates to reduce similarity
    templates = [
        "{emoji} {title}\n\n{snippet} {cta}\n\n",
        "{emoji} 🚨 {title}\n\n{snippet} {cta}\n\n",
        "{emoji} What's new in {keyword}? {title}\n\n{snippet} {cta}\n\n",
        "{emoji} Big update! {title}\n\n{snippet} {cta}\n\n",
        "{emoji} {keyword} alert: {title}\n\n{snippet} {cta}\n\n",
        "{emoji} Curious? {title}\n\n{snippet} {cta}\n\n",
    ]

    # CTAs to encourage engagement
    ctas = [
        "Read more! 👇",
        "Your thoughts? 🤔",
        "Check it out! 🔍",
        "Join the convo! 💬",
        "See the details! 🚀",
        "What's your take? 🗳️",
    ]

    # Extract and clean snippet
    snippet = (
        article.get("snippet") or article.get("summary", "") or "No summary available."
    )
    snippet = snippet.replace("\n", " ").strip()  # Remove newlines, clean up
    snippet = (
        snippet[:120] + "..." if len(snippet) > 120 else snippet
    )  # Shorter for natural fit

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

    # Dynamic hashtags (limited to 2 to avoid spam flags)
    dynamic_tags = []
    if post_keywords:
        unique_keywords = list(dict.fromkeys(post_keywords))[
            :2
        ]  # Limit to 2, preserve order
        dynamic_tags = [
            "#" + "".join(c for c in kw if c.isalnum()) for kw in unique_keywords
        ]

    # Combine tags, but cap total hashtags
    all_tags = (base_tags + " " + " ".join(dynamic_tags)).strip()
    if not dynamic_tags:
        all_tags = base_tags

    # Validate and set link
    url = article.get("link", "")
    article_link = None
    if url:
        try:
            if urllib.request.urlopen(url).getcode() == 200:
                article_link = url
        except Exception:
            article_link = None

    # Choose template and CTA
    template = random.choice(templates)
    cta = random.choice(ctas)

    # Only use "No link available" if there is no link at all
    if article_link:
        link_for_post = article_link
    elif not url:
        link_for_post = "No link available"
    else:
        link_for_post = ""

    # Generate post text (no full_text embedding to avoid length issues)
    post_text = template.format(
        emoji=selected_emoji,
        title=article.get("title", "Untitled"),
        snippet=snippet,
        cta=cta,
        keyword=selected_keyword.capitalize(),
    )

    # Add hashtags only if they fit within 280 chars (excluding link)
    post_text_with_tags = f"{post_text}\n\n{all_tags}"
    if len(post_text_with_tags) <= 280:
        post_text = post_text_with_tags
    else:
        # If tags push over limit, prioritize content
        post_text = post_text[:277] + "..."

    # Ensure final text is within 280 chars
    post_text = post_text[:277] + "..." if len(post_text) > 280 else post_text

    # Pick image based on keywords
    image_path = pick_image(post_keywords) if post_keywords else None

    # Return the link separately
    return {
        "text": post_text,
        "image_path": image_path,
        "recommended_delay": random.uniform(30, 120),  # Suggest delay for pipeline
        "link": article_link if article_link else (url if url else None),
    }
