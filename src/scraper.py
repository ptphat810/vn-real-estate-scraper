import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from parser import parse_detail_page, get_post_id, classify_transaction_type
from utils import get_logger, save_data

logger = get_logger("scraper")


def safe_quit_driver(self):
    try:
        self.quit()
    except:
        pass
uc.Chrome.__del__ = safe_quit_driver


def init_browser(headless=True):
    logger.info("Initializing driver...")
    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_argument(f'--user-agent={user_agent}')

    try:
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(60)
        return driver

    except Exception as e:
        logger.error(f"Failed to initialize driver: {e}")
        raise


def fetch_list_links(driver, page_url, mongo_client):
    logger.info(f"Scanning: {page_url}")
    links = []
    skipped = 0

    try:
        driver.get(page_url)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "js__card")))
        items = driver.find_elements(By.CLASS_NAME, "js__card")
        type_post = classify_transaction_type(page_url)
        count = len(items)

        for item in items:
            try:
                link_tag = item.find_element(By.TAG_NAME, "a")
                url = link_tag.get_attribute("href")
                pid = get_post_id(url)

                if pid and not mongo_client.check_duplicated(pid, type_post):
                    links.append((url, pid))
                else:
                    skipped += 1

            except (NoSuchElementException, StaleElementReferenceException):
                continue

        logger.info(f"Fetched {len(links)} new links from list page (Skipped {skipped} duplicates)")
    except Exception as e:
        logger.error(f"Error fetching list links: {e}")

    return links, skipped


def process_single_page(driver, links, mongo_client):
    count = 0
    for i, (url, pid) in enumerate(links):
        try:
            logger.info(f"Processing detail [{i + 1}/{len(links)}]: {pid}")
            driver.get(url)

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.re__pr-title"))
            )

            html_content = driver.page_source
            data = parse_detail_page(html_content, url)
            if data is not None:
                save_data([data])
                mongo_client.insert_post(data)
                count += 1

                logger.info(f"--> Saved {pid} to MongoAtlas")

            time.sleep(random.uniform(2, 4))
        except Exception as e:
            logger.warning(f"--> Skipping {pid} due to error: {e}")
    return count


def process_multiple_pages(driver, target, mongo_client):
    name = target.get("name")
    base_url = target.get("url")
    start_page = target.get("start_page", 1)
    end_page = target.get("end_page", 2)

    total_new = 0
    total_skipped = 0
    pages_processed = 0

    logger.info(f"=== PROCESSING TARGET: {name.upper()} ===")

    for p in range(start_page, end_page + 1):
        page_url = base_url if p == 1 else f"{base_url}/p{p}"
        logger.info(f"=== ACCESSING PAGE {p} ===")

        links, skipped = fetch_list_links(driver, page_url, mongo_client)
        total_skipped += skipped

        if not links:
            logger.info(f"No new links found on page {p}.")
            pages_processed += 1
            continue

        inserted_count = process_single_page(driver, links, mongo_client)
        total_new += inserted_count

        pages_processed += 1
        time.sleep(random.uniform(3, 6))

    return total_new, total_skipped, pages_processed