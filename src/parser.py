from bs4 import BeautifulSoup
import re
import unidecode
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from utils.logger import get_logger

logger = get_logger("parser")

# Property type mapping for sale listings
SALE_PROPERTY_TYPES = {
    "ban-can-ho-chung-cu": "Apartment",
    "ban-can-ho-chung-cu-mini": "Mini Apartment",
    "ban-nha-rieng": "Private House",
    "ban-nha-biet-thu-lien-ke": "Villa/Townhouse",
    "ban-nha-mat-pho": "Storefront House",
    "ban-shophouse-nha-pho-thuong-mai": "Shophouse",
    "ban-dat-nen-du-an": "Project Land",
    "ban-dat": "Land Plot",
    "ban-trang-trai-khu-nghi-duong": "Farm/Resort",
    "ban-condotel": "Condotel",
    "ban-kho-nha-xuong": "Warehouse/Factory"
}

# Property type mapping for rental listings
RENT_PROPERTY_TYPES = {
    "cho-thue-can-ho-chung-cu": "Apartment",
    "cho-thue-can-ho-chung-cu-mini": "Mini Apartment",
    "cho-thue-nha-rieng": "Private House",
    "cho-thue-nha-biet-thu-lien-ke": "Villa/Townhouse",
    "cho-thue-nha-mat-pho": "Storefront House",
    "cho-thue-shophouse-nha-pho-thuong-mai": "Shophouse",
    "cho-thue-dat": "Land Plot",
    "cho-thue-trang-trai-khu-nghi-duong": "Farm/Resort",
    "cho-thue-condotel": "Condotel",
    "cho-thue-kho-nha-xuong": "Warehouse/Factory",
    "cho-thue-van-phong": "Office Space",
    "cho-thue-cua-hang-ki-ot": "Shop/Kiosk",
    "cho-thue-phong-tro": "Room"
}

# Combined mapping for unified lookup
ALL_PROPERTY_TYPES = {**SALE_PROPERTY_TYPES, **RENT_PROPERTY_TYPES}

# Transaction type detection patterns
TRANSACTION_TYPE_PATTERNS = {
    "sale": r'^ban-',
    "rent": r'^cho-thue-'
}

SPEC_KEY_MAPPING = {
    "khoang_gia": "price",
    "dien_tich": "area",
    "so_phong_ngu": "bedroom",
    "so_phong_tam_ve_sinh": "bathroom",
    "so_tang": "num_floor",
    "huong_nha": "orientation",
    "huong_ban_cong": "balcony_direction",
    "mat_tien": "front_width",
    "duong_vao": "road_width",
    "phap_ly": "legal",
    "noi_that": "furniture",
    "thoi_gian_du_kien_vao_o": "exdate",
    "muc_gia_dien": "electricity",
    "muc_gia_nuoc": "water",
    "muc_gia_internet": "internet",
    "tien_ich": "utilities"
}

# Pre-compiled regex patterns
POST_ID_PATTERN = re.compile(r"pr(\d+)$")


def normalize_key(key: str) -> str:
    """
    Convert to lowercase, remove accents, replace spaces with underscores,
    and remove special characters.
    """
    key = unidecode.unidecode(key).lower()

    # Replace spaces and commas with underscores
    key = re.sub(r'[\s,]+', '_', key)

    # Remove other special characters (keep only alphanumeric and underscores)
    key = re.sub(r'[^\w_]', '', key)

    # Collapse multiple consecutive underscores into a single one
    key = re.sub(r'_+', '_', key)

    # Trim leading and trailing underscores
    key = key.strip('_')

    return key


def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively remove None values, empty collections,
    and empty strings from a dictionary.
    """
    cleaned = {}

    for key, value in data.items():
        # Skip None values
        if value is None:
            continue

        # Skip empty strings or strings containing only whitespace
        if isinstance(value, str) and not value.strip():
            continue

        # Recursively clean nested dictionaries
        if isinstance(value, dict):
            cleaned_nested = clean_dict(value)
            if cleaned_nested:
                cleaned[key] = cleaned_nested
            continue

        # Skip empty lists
        if isinstance(value, list) and not value:
            continue

        cleaned[key] = value

    return cleaned


def get_text(soup: BeautifulSoup, selector: str, default: Optional[str] = None) -> Optional[str]:
    """
    Safely extract text content from HTML element by CSS selector.
    """
    tag = soup.select_one(selector)
    return tag.get_text(strip=True) if tag else default


def get_post_id(url: str) -> Optional[str]:
    """Extract the unique post identifier from listing URL."""
    match = POST_ID_PATTERN.search(url)
    return match.group(1) if match else None


def set_property_category(url: str) -> str:
    """Determine property category from URL path segment."""
    path = urlparse(url).path.strip('/').lower()

    # Match the longest key first
    sorted_types = sorted(
        ALL_PROPERTY_TYPES.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    for path_segment, category in sorted_types:
        if path.startswith(path_segment):
            # Verify path segment boundary
            is_full_match = len(path) == len(path_segment)
            if is_full_match or path[len(path_segment)] in ('-', '/'):
                return category

    return "Unknown"


def set_transaction_type(url: str) -> str:
    """Detect the transaction type (sale or rent) from URL pattern."""
    path = urlparse(url).path.strip('/').lower()

    for transaction_type, pattern in TRANSACTION_TYPE_PATTERNS.items():
        if re.match(pattern, path):
            return transaction_type

    return "Unknown"


def get_coordinate(html_content: str) -> Dict[str, float]:
    """
    Uses flexible Regex to extract key numerical values coordinates
    from a hidden JavaScript configuration block in the static HTML
    """
    geo = {}
    keys = ['latitude', 'longitude']

    for key in keys:
        pattern = rf'["\']?{re.escape(key)}["\']?\s*:\s*(-?[\d\.]+)'
        match = re.search(pattern, html_content)
        if match:
            try:
                geo[key] = float(match.group(1).replace(' ', ''))
            except ValueError:
                pass

    return geo


def get_specs(soup: BeautifulSoup) -> Dict[str, str]:
    specs = {}

    items = soup.select(".re__pr-specs-content-item")
    if not items:
        return specs

    for item in items:
        label_tag = item.select_one(".re__pr-specs-content-item-title")
        value_tag = item.select_one(".re__pr-specs-content-item-value")

        if label_tag and value_tag:
            key = normalize_key(label_tag.get_text(strip=True))
            value = value_tag.get_text(strip=True)
            specs[key] = value

    return specs


def get_sub_info(soup: BeautifulSoup) -> Dict[str, str]:
    sub_info = {}

    items = soup.select("div.re__pr-short-info-item")
    if not items:
        return sub_info

    for item in items:
        title_tag = item.select_one("span.title")
        value_tag = item.select_one("span.value")

        if title_tag and value_tag:
            key = normalize_key(title_tag.get_text(strip=True))
            value = value_tag.get_text(strip=True)
            sub_info[key] = value

    return sub_info


def get_agent_info(soup: BeautifulSoup) -> Dict[str, str]:
    agent_info = {}

    # Locate the main contact container
    contact_box = soup.find("div", class_="re__ldp-contact-box")
    if not contact_box:
        return agent_info

    # Extract agent name and profile link
    agent_infor = contact_box.find("div", class_="re__agent-infor re__agent-name")
    if agent_infor:
        name_tag = (
                agent_infor.find("a", class_="re__contact-name") or
                agent_infor.find("a", class_="js__agent-contact-name")
        )
        if name_tag:
            agent_info['name'] = name_tag.get_text(strip=True)
            href = name_tag.get('href')
            if href:
                agent_info['profile_url'] = href

    # Extract agent avatar image URL
    avatar_tag = soup.select_one("img.re__contact-avatar")
    if avatar_tag:
        src = avatar_tag.get('src')
        if src:
            agent_info['avatar_url'] = src

    # Extract invisible phone number
    phone_tag = soup.select_one("div.js__phone")
    if phone_tag:
        phone_span = phone_tag.find('span')
        if phone_span:
            agent_info['phone_invisible'] = phone_span.get_text(strip=True)

    # Extract Zalo messaging contact information
    zalo_tag = soup.select_one("a.js__zalo-chat")
    if zalo_tag:
        data_href = zalo_tag.get('data-href')
        if data_href:
            agent_info['zalo_url'] = data_href

    # Extract other information
    other_agent_info = soup.select("div.re__agent-experiment div.agent-deail-infor")
    for item in other_agent_info:
        label_tag = item.select_one("span")
        value_tag = item.select_one("i")

        if label_tag and value_tag:
            label = label_tag.get_text(strip=True).lower()
            value = value_tag.get_text(strip=True)

            if "tham gia" in label:
                agent_info["join_duration"] = value
            elif "tin đăng" in label:
                agent_info["listings"] = value

    return agent_info


def get_project_info(soup: BeautifulSoup) -> Dict[str, str]:
    project_info = {}

    card = soup.select_one("div.re__ldp-project-info")
    if not card:
        return project_info

    # Extract project name
    title = get_text(card, "div.re__project-title")
    if title:
        project_info["name"] = title

    # Extract status
    for item in card.select("span.re__prj-card-config-value"):
        text = item.get_text(strip=True)
        aria_label = unidecode.unidecode(item.get("aria-label", "")).lower()

        if "trang thai" in aria_label:
            project_info["status"] = text
        elif "gia" in aria_label:
            project_info["price"] = text

    # Extract investor information
    investor = get_text(card, "span.re__prj-card-config-value i.re__icon-office--sm + span.re__long-text")
    if investor:
        project_info["investor"] = investor

    # Extract project image
    img = card.select_one("div.re__section-avatar img")
    if img:
        src = img.get("src")
        if src:
            project_info["image"] = src

    # Extract project URL
    link = card.select_one("div.re__section-avatar a")
    if link:
        href = link.get("href")
        if href:
            project_info["project_url"] = href

    # Extract listing count
    a_tag = card.select_one("a.re__link-pr span")
    if a_tag:
        text = a_tag.get_text(strip=True)
        match = re.search(r'\d+', text.replace(',', ''))
        if match:
            project_info["listing_count"] = int(match.group())

    return project_info


def get_description(soup: BeautifulSoup) -> Optional[str]:
    prefix = "Thông tin mô tả"
    description_tag = soup.select_one(".re__pr-description")
    if not description_tag:
        return None

    description = description_tag.get_text(strip=True)

    # Remove standard prefix
    if description.startswith(prefix):
        description = description[len(prefix):].strip()

    return description if description else None


def get_images(soup: BeautifulSoup) -> List[str]:
    images = []

    for item in soup.select("div.re__media-thumb-item.js__media-thumbs-item"):
        img_tag = item.find("img")
        if img_tag:
            # Prefer data-src for lazy-loaded images
            img_url = img_tag.get("data-src") or img_tag.get("src")
            if img_url:
                images.append(img_url)

    return images


def parse_detail_page(html_content: str, url: str) -> Dict[str, Any]:
    """
    Parse a property listing page into structured data
    Args:
        html_content: Raw HTML content of the listing page
        url: URL of the listing page being parsed
    Returns:
        Dictionary containing structured property data
    """
    post_id = get_post_id(url) or "UnknownID"
    try:
        soup = BeautifulSoup(html_content, "lxml")
    except Exception as e:
        logger.critical(f"[{post_id}] Failed to initialize BeautifulSoup: {e}", exc_info=True)
        return {}

    try:
        title = get_text(soup, "h1")
        address = get_text(soup, "span.re__pr-short-description")
        price_per_spm = get_text(soup, "span.ext")
        description = get_description(soup)
        images = get_images(soup)
    except Exception as e:
        logger.warning(f"[{post_id}] Error in basic info extraction: {e}")
        title, address, price_per_spm, description, images = None, None, None, None, []

    coords = {}
    try:
        coords = get_coordinate(html_content)
    except Exception as e:
        logger.debug(f"[{post_id}] Could not extract coordinates: {e}")

    specs = {}
    spec_data = {}
    sub_info = {}
    try:
        specs = get_specs(soup)
        sub_info = get_sub_info(soup)

        for key, value in specs.items():
            mapped_key = SPEC_KEY_MAPPING.get(key, key)
            if mapped_key not in ['price', 'area']:
                spec_data[mapped_key] = value
    except Exception as e:
        logger.error(f"[{post_id}] Failed to parse specs table: {e}")

    agent_info = {}
    try:
        agent_info = get_agent_info(soup)
    except Exception as e:
        logger.warning(f"[{post_id}] Agent info extraction failed: {e}")

    # Construct final data structure
    try:
        data = {
            "post_id": post_id if post_id != "UnknownID" else None,
            "property_url": url,
            "transaction_type": set_transaction_type(url),
            "property_category": set_property_category(url),
            "title": title,
            "address": address,
            "latitude": coords.get('latitude'),
            "longitude": coords.get('longitude'),
            "price": specs.get("khoang_gia"),
            "price_per_spm": price_per_spm,
            "area": specs.get("dien_tich"),
            "spec": spec_data,
            "description": description,
            "images": images,
            "date_posted": sub_info.get("ngay_dang"),
            "date_expired": sub_info.get("ngay_het_han"),
            "news_type": sub_info.get("loai_tin"),
            "contact_info": agent_info,
            "scraped_at": datetime.now().isoformat()
        }

        return clean_dict(data)
    except Exception as e:
        logger.error(f"[{post_id}] Unexpected error during data assembly: {e}", exc_info=True)
        return {"post_id": post_id, "property_url": url, "error": str(e)}