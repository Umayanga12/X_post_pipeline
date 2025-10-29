
# summarize_article_social.py
from langchain_ollama import ChatOllama
from config import logger


def summarize_article(article_text: str) -> str:
    """
    Create a short, impactful, and engaging crypto news post suitable for social media.
    This version uses enhanced prompt engineering for better hooks and readability.
    """
    try:
        llm = ChatOllama(
            model="hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF",
            temperature=0.9,  # slightly higher for engaging tone
        )

        system_prompt = f"""
You are a professional **crypto journalist and social media strategist** writing for a global audience.

🎯 **Your mission:**
Transform the given crypto article into a short *insight-driven post* (not a summary).
Make it sound like breaking news or a strong insight — something people want to share.

🧠 **Guidelines:**
- Don’t summarize — *reinterpret* it in a way that highlights the key insight, trend, or impact.
- Keep all essential facts accurate (e.g., prices, partnerships, regulations, etc.)
- Focus on *what makes it important or surprising* to the crypto community.
- Avoid robotic phrasing like “The article discusses…” or “This report says…”
- Write in a confident, journalistic tone — as if from CoinDesk or The Block.
- Avoid hashtags, emojis, or links.
- Use strong openers like “Breaking:”, “Update:”, “Analysts note that…”, or “New development:”
- Length: 50–100 words max.

💡 **Examples:**
1️⃣ *Breaking:* Ethereum’s latest upgrade boosts scalability by 20%, setting the stage for mass DeFi adoption. Developers say this could redefine transaction efficiency across Layer-2 chains.  
2️⃣ Bitcoin miners are seeing profit surges after the halving — despite energy costs climbing. The network’s resilience shows investor confidence remains strong.  
3️⃣ Ripple gains momentum as another central bank explores its blockchain for digital currencies — a quiet but powerful move toward institutional adoption.

📰 **Article:**
\"\"\"{article_text}\"\"\"

✍️ Now craft one powerful social-media-ready post:
"""

        response = llm.invoke(system_prompt)

        summary = (
            response.strip()
            if isinstance(response, str)
            else getattr(response, "content", "").strip()
        )

        # Cleanup unwanted prefixes or meta language
        summary_lines = summary.split("\n")
        cleaned_summary = " ".join(
            line.strip()
            for line in summary_lines
            if line.strip()
            and not line.lower().startswith(("here is", "summary:", "this article"))
        )

        # Ensure concise tweet-style limit
        if len(cleaned_summary) > 280:
            cleaned_summary = cleaned_summary[:277].rsplit(" ", 1)[0] + "…"

        if not cleaned_summary:
            raise ValueError("No valid summary extracted")

        return cleaned_summary

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return article_text[:200]

