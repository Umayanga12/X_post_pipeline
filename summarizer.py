# This file handles article summarization using Ollama.
from langchain_ollama import ChatOllama
from config import logger


def summarize_article(article_text: str) -> str:
    try:
        llm = ChatOllama(
            model="hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF", temperature=0.7
        )
        system_prompt = f"Summarize this article in 3-4 sentences (focus on key insights, keep only important details):\n\n{article_text}"
        response = llm.invoke(system_prompt)

        # Handle response (could be string or dict with 'content' key)
        if isinstance(response, str):
            summary = response.strip()
        elif hasattr(response, "content"):
            summary = response.content.strip()
        else:
            raise ValueError("Unexpected response format from LLM")

        # Remove any leading metadata or prompts (e.g., "Here is a 4-sentence summary:")
        summary_lines = summary.split("\n")
        cleaned_summary = " ".join(
            line.strip()
            for line in summary_lines
            if line.strip()
            and not line.strip().startswith(("Here is", "Key insights:"))
        )
        if not cleaned_summary:
            raise ValueError("No valid summary extracted")

        return cleaned_summary
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return article_text[:200]  # Fallback to truncated text
