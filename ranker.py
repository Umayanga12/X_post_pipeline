from langchain_ollama import ChatOllama
from config import logger


def Rank_News_Items(news_items):
    """
    Given a list of news items (dicts), ask LLM to rank and return top 3 dicts.
    """
    logger.info("Ranking news items...")
    print(news_items)
    try:
        llm = ChatOllama(
            model="hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF",
            temperature=0.3,
        )

        # Create a mapping from string summary to article dict
        item_to_dict = {}
        formatted_items = []
        for i, item in enumerate(news_items):
            # Use title + snippet for ranking string
            summary = f"{item.get('title', '')}: {item.get('snippet', item.get('summary', ''))}"
            formatted_items.append(f"{i + 1}. {summary}")
            item_to_dict[str(i + 1)] = item  # Map index to dict

        formatted_str = "\n".join(formatted_items)

        system_prompt = f"""
You are a news ranking assistant. Rank the following crypto/web3/blockchain news items
by their importance and relevance for investors and traders.
Return ONLY the top 3 items, no extra text.

News items:
{formatted_str}
"""

        response = llm.invoke(system_prompt)

        # Extract text depending on type of response
        if hasattr(response, "content"):
            ranked_text = response.content.strip()
        else:
            ranked_text = str(response).strip()

        # Extract the indices of the top 3 items
        top_indices = []
        for line in ranked_text.split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                idx = line.split(".", 1)[0]
                if idx in item_to_dict:
                    top_indices.append(idx)
            if len(top_indices) >= 3:
                break

        # Return the original dicts in ranked order
        return [item_to_dict[idx] for idx in top_indices]

    except Exception as e:
        logger.error(f"Ranking error: {e}")
        # Fallback: just return first 3 items
        return news_items[:3]
