import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from parser import parse_detail_page, get_post_id
from utils import is_success, update_status, get_logger

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
        logger.error(f"Failed to initialize Driver: {e}")
        raise


def fetch_list_links(driver, page_url):
    logger.info(f"Scanning: {page_url}")
    links = []
    skipped_on_page = 0

    try:
        driver.get(page_url)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "js__card")))
        items = driver.find_elements(By.CLASS_NAME, "js__card")
        count_on_page = len(items)

        for item in items:
            try:
                link_tag = item.find_element(By.TAG_NAME, "a")
                url = link_tag.get_attribute("href")
                pid = get_post_id(url)

                if pid:
                    if not is_success(pid):
                        links.append((url, pid))
                    else:
                        skipped_on_page += 1
            except (NoSuchElementException, StaleElementReferenceException):
                continue

        logger.info(f"Page stats: {count_on_page} items found, {len(links)} are new.")
    except Exception as e:
        logger.error(f"Error fetching links at {page_url}: {e}")

    return links, skipped_on_page


def process_single_page(driver, links):
    page_data = []
    total = len(links)

    for i, (url, pid) in enumerate(links):
        logger.info(f"[{i + 1}/{total}] Processing ID: {pid}")
        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.re__pr-title"))
            )

            html_content = driver.page_source
            data = parse_detail_page(html_content, url)

            if data:
                page_data.append(data)
                category = data.get("transaction_type")
                update_status(pid, url, "success", category)
                logger.info(f"-> Success data extracted")

            time.sleep(random.uniform(2, 4))
        except Exception as e:
            logger.warning(f"-> Skip {pid} due to error: {e}")

    return page_data


def process_multiple_pages(driver, target, save_data_fn):
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

        links, skipped = fetch_list_links(driver, page_url)
        total_skipped += skipped

        if not links:
            pages_processed += 1
            continue

        results = process_single_page(driver, links)

        if results:
            save_data_fn(results)
            total_new += len(results)

        pages_processed += 1
        time.sleep(random.uniform(3, 6))

    return total_new, total_skipped, pages_processed