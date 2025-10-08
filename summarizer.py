# summarize_article_social.py
from langchain_ollama import ChatOllama
from config import logger


def summarize_article(article_text: str) -> str:
    """
    Generate a social-media-friendly summary suitable for posting on X (Twitter).
    The summary will be concise, engaging, and insight-focused — no meta language.
    """
    try:
        llm = ChatOllama(
            model="hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF",
            temperature=0.8,  # slightly higher to get creative phrasing
        )

        system_prompt = f"""
You are a professional social media content strategist.

Your task:
- Summarize the following article into a single short post (max 280 characters).
- The post should sound natural and engaging, not like an academic summary.
- Avoid phrases like "This article discusses..." or "The article is about...".
- Focus on *what matters most* — key insight, impact, or surprising fact.
- If relevant, make it catchy, thought-provoking, or shareable.
- Don't include hashtags, links, or emojis.

Article:
\"\"\"{article_text}\"\"\"

Now write the post-ready summary:
"""

        response = llm.invoke(system_prompt)

        # Handle Ollama response
        summary = (
            response.strip()
            if isinstance(response, str)
            else getattr(response, "content", "").strip()
        )

        # Cleanup any unwanted prefixes
        summary_lines = summary.split("\n")
        cleaned_summary = " ".join(
            line.strip()
            for line in summary_lines
            if line.strip()
            and not line.lower().startswith(("here is", "summary:", "this article"))
        )

        # Ensure reasonable length
        if len(cleaned_summary) > 280:
            cleaned_summary = cleaned_summary[:277].rsplit(" ", 1)[0] + "…"

        if not cleaned_summary:
            raise ValueError("No valid summary extracted")

        return cleaned_summary

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        # fallback to truncated version
        return article_text[:200]
