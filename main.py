import queue
import time
import random
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from config import logger, POST_QUEUE_SIZE, RSS_URLS, SCRAPE_BASE_URLS
from fetcher import fetch_from_rss, scrape_articles, extract_article_content
from deduper import is_duplicate, save_posted
from ranker import Rank_News_Items
from summarizer import summarize_article
from post_generator import (
    generate_post,
)  # Assumes this returns {"text": ..., "image_path": ..., "recommended_delay": ...}
from poster import post_to_x

# Queues
article_queue = queue.Queue(maxsize=POST_QUEUE_SIZE)  # Queue for articles to process
post_queue = queue.Queue(maxsize=POST_QUEUE_SIZE)  # Queue for ready posts


def post_to_x_with_retry(post: dict, max_retries: int = 2) -> bool:
    """Wrapper for post_to_x with retries on 403 errors."""
    for attempt in range(max_retries + 1):
        success = post_to_x(post)
        if success:
            return True
        if attempt < max_retries:
            # Exponential backoff: 60s * (2 ** attempt)
            retry_delay = 60 * (2**attempt) + random.uniform(0, 30)
            logger.warning(
                f"Post attempt {attempt + 1} failed (likely 403 spam flag). Retrying in {retry_delay:.0f}s..."
            )
            time.sleep(retry_delay)
    logger.error("All post retries failed.")
    return False


def pipeline_job():
    logger.info("Running pipeline job...")

    # Step 1: Fetch articles
    rss_articles = fetch_from_rss(RSS_URLS)
    scraped_articles = scrape_articles(SCRAPE_BASE_URLS)
    all_articles = rss_articles + scraped_articles
    logger.info(
        f"Fetched {len(all_articles)} total articles ({len(rss_articles)} RSS, {len(scraped_articles)} scraped)"
    )

    if not all_articles:
        logger.info("No new articles found; skipping post.")
        return

    processed_count = 0
    logger.info("Processing articles....")

    # Step 2: Process articles
    for article in all_articles:
        full_text = article.get("full_text")
        if not full_text:
            extract_result = extract_article_content(article["link"])
            if extract_result.get("success"):
                full_text = extract_result.get("text")
                article["full_text"] = full_text
                article["snippet"] = extract_result.get("summary", "")
                logger.info(
                    f"Extracted full text for: {article.get('title', '')[:50]}..."
                )

        if full_text:
            logger.info("Handling duplicates....")
            if is_duplicate(full_text):
                logger.info(f"Skipping duplicate: {article.get('title', '')[:50]}...")
                continue
            if "snippet" in article and len(article["snippet"]) > 200:
                article["snippet"] = summarize_article(full_text)
            article_queue.put(article)
            processed_count += 1
            logger.info(f"Queued article: {article.get('title', '')[:50]}...")

    logger.info(f"Processed {processed_count} unique articles")

    if article_queue.empty():
        logger.info("No unique articles after processing; skipping.")
        return

    # Step 3: Rank articles
    articles_to_rank = []
    while not article_queue.empty():
        articles_to_rank.append(article_queue.get())
    ranked_articles = Rank_News_Items(articles_to_rank)
    logger.info(f"Ranked {len(ranked_articles)} articles")
    print(ranked_articles)

    # Limit to top N articles to avoid spam flags from too many similar posts
    MAX_POSTS_PER_RUN = 3  # Adjust based on testing (start low)
    ranked_articles = ranked_articles[:MAX_POSTS_PER_RUN]
    logger.info(f"Limited to top {len(ranked_articles)} articles for posting.")

    # Step 4: Generate posts after ranking
    for article in ranked_articles:
        post = generate_post(article)
        post_queue.put(post)
        logger.info(f"Generated post for: {post.get('text', '')[:50]}...")

    print("=================================================")
    # Drain queue for logging (optional)
    generated_posts = []
    while not post_queue.empty():
        generated_posts.append(post_queue.get())
    print(generated_posts)

    # Step 5: Post to X with delays and retries
    posted_count = 0
    for idx, post in enumerate(generated_posts):
        success = post_to_x_with_retry(post)
        if success:
            # Save only on final success (adjust if save_posted uses url/full_text)
            url = post.get(
                "url", ""
            )  # Assuming post has these; add if needed in generate_post
            full_text = post.get("full_text", "")
            save_posted(url, full_text)
            posted_count += 1
            logger.info(
                f"Successfully posted (total so far: {posted_count}/{len(generated_posts)})"
            )
        else:
            logger.error("Post failed after retries - check logs above")

        # Delay before next post to mimic human behavior and avoid spam detection
        if idx < len(generated_posts) - 1:  # No delay after last post
            delay = post.get(
                "recommended_delay", random.uniform(60, 180)
            )  # 1-3 min default
            logger.info(
                f"⏳ Delaying {delay:.0f}s before next post to avoid spam flags..."
            )
            time.sleep(delay)

    if posted_count == 0:
        logger.warning("No posts sent - either no unique articles or posting errors")
    else:
        logger.info(
            f"Pipeline complete: {posted_count}/{len(generated_posts)} posts sent successfully"
        )


if __name__ == "__main__":
    pipeline_job()
    scheduler = BlockingScheduler()

    # Schedule the pipeline to run every hour
    _ = scheduler.add_job(
        pipeline_job,
        trigger=CronTrigger(hour="6", minute=0),  # Run at the start of every hour
        id="pipeline_job",
        max_instances=1,
        replace_existing=True,
    )
    logger.info("Starting APScheduler for hourly pipeline execution...")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down APScheduler...")
        scheduler.shutdown()
        logger.info("Pipeline stopped.")
