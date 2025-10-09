import queue
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from config import logger, POST_QUEUE_SIZE, RSS_URLS, SCRAPE_BASE_URLS
from fetcher import fetch_from_rss, scrape_articles, extract_article_content
from deduper import is_duplicate, save_posted
from ranker import Rank_News_Items
from summarizer import summarize_article
from post_generator import generate_post
from poster import post_to_x

# Queues
article_queue = queue.Queue(maxsize=POST_QUEUE_SIZE)  # Queue for articles to process
post_queue = queue.Queue(maxsize=POST_QUEUE_SIZE)  # Queue for ready posts


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
    posted_count = 0
    logger.info("processing aricals....")
    # Step 2: Process articles
    for article in all_articles:
        full_text = article.get("full_text")
        if not full_text:
            extract_result = extract_article_content(article["link"])
            if extract_result["success"]:
                full_text = extract_result["text"]
                article["full_text"] = full_text
                article["snippet"] = extract_result["summary"]
                logger.info(f"Extracted full text for: {article['title'][:50]}...")
        logger.info("Handling duplicates....")
        if full_text:
            if is_duplicate(full_text):
                logger.info(f"Skipping duplicate: {article['title'][:50]}...")
                continue
            if len(article["snippet"]) > 200:
                article["snippet"] = summarize_article(full_text)
            article_queue.put(article)
            processed_count += 1
            logger.info(f"Queued article: {article['title'][:50]}...")

    logger.info(f"Processed {processed_count} unique articles")

    # Step 3: Rank articles
    articles_to_rank = []
    while not article_queue.empty():
        articles_to_rank.append(article_queue.get())
    ranked_articles = Rank_News_Items(articles_to_rank)
    logger.info(f"Ranked {len(ranked_articles)} articles")
    print(ranked_articles)

    # Step 4: Generate posts after ranking
    generated_posts = []
    for article in ranked_articles:
        post = generate_post(article)
        post_queue.put(post)
        generated_posts.append(post)
        logger.info(f"Generated post for: {post['text'][:50]}...")

    print("=================================================")
    print(generated_posts)

    # Step 5: Post to X
    for post in generated_posts:
        if post_to_x(post):
            save_posted(post["url"], post["full_text"])
            posted_count += 1
            logger.info(f"Successfully posted: {len(generated_posts)} total")
        else:
            logger.error("Post failed - check logs above")

    if posted_count == 0:
        logger.warning("No posts sent - either no unique articles or posting errors")


if __name__ == "__main__":
    scheduler = BlockingScheduler()

    # Schedule the pipeline to run every hour
    scheduler.add_job(
        pipeline_job,
        trigger=CronTrigger(hour="*", minute=0),  # Run at the start of every hour
        id="pipeline_job",
        max_instances=1,
        replace_existing=True,
    )
    pipeline_job()
    logger.info("Starting APScheduler for hourly pipeline execution...")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down APScheduler...")
        scheduler.shutdown()
        logger.info("Pipeline stopped.")
