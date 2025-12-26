import time
from src.mongo_client import MongoDBClient
from src.scraper import init_browser, process_multiple_pages
from src.utils import load_config, get_logger

logger = get_logger("main")

def main():
    logger.info("=== STARTING SCRAPER SYSTEM ===")

    mongo = None
    driver = None
    total_new_records = 0
    total_skipped = 0
    pages_processed = 0
    start_time = time.time()

    try:
        mongo = MongoDBClient()
        cfg = load_config()
        sc_cfg = cfg.get('scraper', {})
        targets = cfg.get('targets', [])

        if not targets:
            logger.error("No targets found in config.yaml")
            return

        driver = init_browser(headless=sc_cfg.get('headless', False))

        for target in targets:
            if not target.get('enabled', True):
                logger.info(f"Skipping disabled target: {target.get('name')}")
                continue

            new_record, skipped_record, page_process = process_multiple_pages(
                driver=driver,
                target=target,
                mongo_client=mongo
            )

            total_new_records += new_record
            total_skipped += skipped_record
            pages_processed += page_process

    except Exception as e:
        logger.critical(f"SYSTEM CRASH: {e}", exc_info=True)

    finally:
        if driver is not None:
            try:
                driver.quit()
                logger.info("Browser closed successfully.")
            except Exception as e:
                logger.warning(f"Failed to close browser: {e}")

        if mongo is not None:
            try:
                mongo.close()
                logger.info("MongoDB connection closed successfully.")

            except Exception as e:
                logger.warning(f"Failed to close MongoDB connection: {e}")

        duration = int(time.time() - start_time)
        minutes, seconds = divmod(duration, 60)

        logger.info(" === SUMMARY ===")
        logger.info(f" Total pages processed: {pages_processed}")
        logger.info(f" Total new records added: {total_new_records}")
        logger.info(f" Total items duplicated: {total_skipped}")
        logger.info(f" Total Duration: {minutes}m {seconds}s")
        logger.info("=== PROCESS FINISHED ===")


if __name__ == "__main__":
    main()