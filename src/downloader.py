import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from parser import parse_detail_page, extract_post_id
from duplicate_filter import is_duplicate, mark_as_scraped
from utils.logging import get_logger

logger = get_logger("crawler")

# Override destructor cho uc.Chrome
def safe_uc_del(self):
    try:
        self.quit()
    except:
        pass
uc.Chrome.__del__ = safe_uc_del

def get_browser(headless=True):
    """ Initializes an anti-bot browser driver. """
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
    """ Scrapes listing URLs and filters duplicates immediately. """
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
                pid = extract_post_id(url)

                if pid:
                    if not is_duplicate(pid):
                        links.append((url, pid))
                    else:
                        skipped_on_page += 1
            except (NoSuchElementException, StaleElementReferenceException):
                continue

        logger.info(f"Page stats: {count_on_page} items found, {len(links)} are new.")
    except Exception as e:
        logger.error(f"Error fetching links at {page_url}: {e}")

    return links, skipped_on_page

def parse(driver, links):
    """ Navigates to each detailed URL, parses content. """
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
                mark_as_scraped(pid)
                logger.info(f"-> Success data extracted")

            time.sleep(random.uniform(2, 4))
        except Exception as e:
            logger.warning(f"-> Skip {pid} due to error: {e}")

    return page_data