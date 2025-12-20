import time
import random
from downloader import get_browser, fetch_list_links, parse
from storage import save_data
from duplicate_filter import load_seen_ids
from utils.logging import get_logger

logger = get_logger("main")


def run_scraper(base_url, start_page=1, end_page=2):
    """ Main workflow with daily file persistence. """
    logger.info("=== STARTING SCRAPER SYSTEM ===")
    driver = get_browser(headless=False)

    # Preloading existing IDs
    seen_ids = load_seen_ids()
    logger.info(f"Loaded {len(seen_ids)} previously saved IDs.")

    start_time = time.time()
    total_new_records = 0
    total_skipped = 0
    pages_processed = 0

    try:
        for p in range(start_page, end_page + 1):
            current_page_url = base_url if p == 1 else f"{base_url}/p{p}"
            logger.info(f"---ACCESSING PAGE {p} ---")

            links, skipped_count = fetch_list_links(driver, current_page_url)
            total_skipped += skipped_count

            if not links:
                logger.info(f"No new items on Page {p}. Moving to next...")
                continue

            results = parse(driver, links)

            if results:
                save_data(results)
                total_new_records += len(results)

            pages_processed += 1
            time.sleep(random.uniform(3, 6))

    except Exception as e:
        logger.critical(f"SYSTEM CRASH: {e}", exc_info=True)
    finally:
        if 'driver' in locals() and driver:
            try:
                logger.info("Closing browser...")
                driver.quit()
            except Exception as e:
                logger.debug(f"Error during driver.quit(): {e}")

        duration_seconds = time.time() - start_time
        minutes, seconds = divmod(int(duration_seconds), 60)

        logger.info(" === SUMMARY ===")
        logger.info(f" Pages attempted: {start_page} to {end_page}")
        logger.info(f" Pages successfully processed: {pages_processed}")
        logger.info(f" Total new records added to JSON: {total_new_records}")
        logger.info(f" Total items skipped (Duplicated): {total_skipped}")
        logger.info(f" Total Duration: {minutes}m {seconds}s")
        logger.info("=== BROWSER CLOSED - PROCESS FINISHED ===")


if __name__ == "__main__":
    TARGET_URL = "https://batdongsan.com.vn/nha-dat-ban"
    # Execute the scraper
    run_scraper(TARGET_URL, start_page=1, end_page=5)