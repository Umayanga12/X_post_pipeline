from langchain_ollama import ChatOllama
from config import logger


def Rank_News_Items(news_items):
    """
    Given a list of news items (strings), ask LLM to rank and return top 3.
    """
    logger.info("Ranking news items...")

    try:
        llm = ChatOllama(
            model="hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF",
            temperature=0.3,  # Lower temp = more consistent ranking
        )

        # Make sure items are formatted as bullet points
        formatted_items = "\n".join(
            f"{i + 1}. {item}" for i, item in enumerate(news_items)
        )

        system_prompt = f"""
You are a news ranking assistant. Rank the following crypto/web3/blockchain news items
by their importance and relevance for investors and traders.
Return ONLY the top 3 items, no extra text.

News items:
{formatted_items}
"""

        response = llm.invoke(system_prompt)

        # Extract text depending on type of response
        if hasattr(response, "content"):
            ranked_text = response.content.strip()
        else:
            ranked_text = str(response).strip()

        # Post-cleaning (ensure we only return top 3 lines)
        top3 = []
        for line in ranked_text.split("\n"):
            if line.strip() and any(ch.isalpha() for ch in line):
                top3.append(line.strip())
            if len(top3) >= 3:
                break

        if not top3:
            raise ValueError("No valid ranked items extracted from LLM response")

        return top3

    except Exception as e:
        logger.error(f"Ranking error: {e}")
        # Fallback: just return first 3 items
        return news_items[:3]
