"""
AnhMin Audio - Link to Text Widget
Lấy nội dung truyện từ các website và biên tập bằng Claude
"""

import os
import re
import time
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QTextEdit, QComboBox, QRadioButton,
    QButtonGroup, QProgressBar, QFileDialog, QMessageBox,
    QCheckBox, QSplitter, QGroupBox, QSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QCursor

from database import db
from api import claude_client
from api.memory_detector import auto_detect_and_add_memory
from api.file_handler import FileHandler
from ui.styles import COLORS

# Check if selenium is available
SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    pass

# Check if BeautifulSoup is available
BS4_AVAILABLE = False
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    pass


def chinese_number_to_int(chinese_num: str) -> int:
    """
    Convert Chinese number to integer.

    Examples:
    - 四千五百三十六 -> 4536
    - 一百二十三 -> 123
    - 五万 -> 50000
    """
    chinese_digits = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9
    }

    chinese_units = {
        '十': 10,
        '百': 100,
        '千': 1000,
        '万': 10000,
        '億': 100000000,
        '亿': 100000000
    }

    result = 0
    current = 0

    for char in chinese_num:
        if char in chinese_digits:
            current = chinese_digits[char]
        elif char in chinese_units:
            unit = chinese_units[char]
            if current == 0:
                current = 1  # Handle cases like 十 (meaning 10, not 0*10)
            if unit >= 10000:  # 万, 億
                result = (result + current) * unit
                current = 0
            else:
                current *= unit
                result += current
                current = 0

    return result + current


def extract_chapter_number(title: str, url: str = "") -> int:
    """
    Extract chapter number from title or URL.

    Supports formats:
    - Chinese numeric: 第1234章
    - Chinese text: 第四千五百三十六章
    - Vietnamese: Chương 123
    - URL: /11337659.html

    Returns the chapter number or 0 if not found.
    """
    # Try to find Chinese chapter number with Arabic numerals: 第1234章
    chinese_digit_pattern = r'第(\d+)章'
    match = re.search(chinese_digit_pattern, title)
    if match:
        return int(match.group(1))

    # Try to find Chinese chapter number with Chinese characters: 第四千五百三十六章
    chinese_text_pattern = r'第([零一二三四五六七八九十百千万億亿]+)章'
    match = re.search(chinese_text_pattern, title)
    if match:
        chinese_num = match.group(1)
        try:
            return chinese_number_to_int(chinese_num)
        except:
            pass  # If conversion fails, continue to other methods

    # Try to find Vietnamese chapter number: Chương 123
    viet_pattern = r'Chương\s+(\d+)'
    match = re.search(viet_pattern, title, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Try to extract from URL (for piaotia: /11337659.html)
    if url:
        url_pattern = r'/(\d{6,})\.html'
        match = re.search(url_pattern, url)
        if match:
            return int(match.group(1))

    return 0


# Supported websites configuration
SUPPORTED_WEBSITES = {
    "truyenphuongdong.com": {
        "name": "Truyện Phương Đông",
        "type": "spa",  # Single Page App - needs Selenium
        "content_selector": "div.chapter-content",
        "title_selector": "h2.chapter-title",
        "next_btn_selector": "a.next-chap",
        "chapter_info_selector": "span.chapter-index",
    },
    "piaotia.com": {
        "name": "飘天文学",
        "type": "static",  # Static HTML - can scrape directly
        "content_selector": None,  # Special: content is text nodes, not in a container
        "title_selector": "h1",
        "encoding": "gbk",
        "special_parser": "piaotia",  # Use custom parser
    },
}


def detect_website(url: str) -> dict:
    """Detect website from URL and return config."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        
        for site_domain, config in SUPPORTED_WEBSITES.items():
            if site_domain in domain:
                return {"domain": site_domain, **config}
        
        return None
    except:
        return None


class StoryInfoWorker(QThread):
    """Worker thread for fetching story information."""
    finished = pyqtSignal(dict)  # {story_name, total_chapters, domain}
    error = pyqtSignal(str)

    def __init__(self, url: str, config: dict):
        super().__init__()
        self.url = url
        self.config = config

    def run(self):
        try:
            if not BS4_AVAILABLE:
                self.error.emit("BeautifulSoup4 chưa được cài đặt")
                return

            domain = self.config.get('domain', '')

            # Check if SPA website first - use Selenium
            if 'truyenphuongdong.com' in domain:
                # This is a SPA website, content is loaded by JavaScript
                # Need Selenium to get info
                if not SELENIUM_AVAILABLE:
                    result = {
                        'story_name': "Cần cài Selenium (pip install selenium webdriver-manager)",
                        'total_chapters': "N/A",
                        'domain': domain
                    }
                    self.finished.emit(result)
                    return

                # Import common Selenium components
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                import time

                # Try using undetected-chromedriver for better anti-bot bypass
                try:
                    import undetected_chromedriver as uc
                    USE_UNDETECTED = True
                except ImportError:
                    USE_UNDETECTED = False
                    from selenium import webdriver
                    from selenium.webdriver.chrome.service import Service
                    from selenium.webdriver.chrome.options import Options
                    from webdriver_manager.chrome import ChromeDriverManager

                driver = None
                try:
                    # Get login credentials from settings
                    from database import db
                    username = db.get_setting('truyenphuongdong_username', '')
                    password = db.get_setting('truyenphuongdong_password', '')

                    if not username or not password:
                        result = {
                            'story_name': "Cần cấu hình tài khoản đăng nhập trong Settings",
                            'total_chapters': "N/A",
                            'domain': domain
                        }
                        self.finished.emit(result)
                        return

                    # Initialize driver based on availability
                    try:
                        if USE_UNDETECTED:
                            # Use undetected-chromedriver
                            options = uc.ChromeOptions()
                            options.add_argument("--headless=new")
                            options.add_argument("--window-size=1920,1080")
                            driver = uc.Chrome(options=options, use_subprocess=True)
                            print("✓ Using undetected-chromedriver")
                        else:
                            # Use regular Selenium
                            chrome_options = Options()
                            chrome_options.add_argument("--headless=new")
                            chrome_options.add_argument("--no-sandbox")
                            chrome_options.add_argument("--disable-dev-shm-usage")
                            chrome_options.add_argument("--disable-gpu")
                            chrome_options.add_argument("--window-size=1920,1080")
                            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

                            service = Service(ChromeDriverManager().install())
                            driver = webdriver.Chrome(service=service, options=chrome_options)
                            print("✓ Using regular Selenium")

                        driver.set_page_load_timeout(30)
                    except Exception as driver_error:
                        print(f"ChromeDriver initialization error: {driver_error}")
                        result = {
                            'story_name': f"Lỗi khởi tạo Chrome: {str(driver_error)[:80]}",
                            'total_chapters': "Cài Chrome và thử lại",
                            'domain': domain
                        }
                        self.finished.emit(result)
                        return

                    # Step 1: Login first
                    login_url = "https://truyenphuongdong.com/login"
                    print(f"Navigating to login page: {login_url}")

                    try:
                        driver.get(login_url)
                        time.sleep(3)
                        print(f"Login page loaded, current URL: {driver.current_url}")
                    except Exception as nav_error:
                        print(f"Error loading login page: {nav_error}")
                        result = {
                            'story_name': f"Không thể tải trang đăng nhập: {str(nav_error)[:60]}",
                            'total_chapters': "Kiểm tra kết nối mạng",
                            'domain': domain
                        }
                        self.finished.emit(result)
                        return

                    try:
                        print("Looking for email field...")
                        # Find and fill email (website uses name="email" not "username")
                        email_field = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.NAME, "email"))
                        )
                        email_field.clear()
                        email_field.send_keys(username)
                        print("Email entered")

                        # Find and fill password
                        print("Looking for password field...")
                        password_field = driver.find_element(By.NAME, "password")
                        password_field.clear()
                        password_field.send_keys(password)
                        print("Password entered")

                        # Submit form
                        print("Looking for submit button...")
                        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                        submit_btn.click()
                        print("Submit button clicked")

                        # Wait for login to complete (check for redirect or cookie)
                        time.sleep(5)

                        # Check if login successful (URL should change from /login)
                        current_url = driver.current_url
                        print(f"After login, current URL: {current_url}")

                        if '/login' in current_url:
                            # Save debug HTML to see error messages
                            try:
                                debug_file = "truyenphuongdong_login_failed.html"
                                with open(debug_file, 'w', encoding='utf-8') as f:
                                    f.write(driver.page_source)
                                print(f"Login failed, saved page to {debug_file}")
                            except:
                                pass

                            result = {
                                'story_name': "Đăng nhập thất bại - kiểm tra username/password",
                                'total_chapters': "Xem console để biết chi tiết",
                                'domain': domain
                            }
                            self.finished.emit(result)
                            return

                        print("Login successful!")

                    except Exception as e:
                        print(f"Login exception: {type(e).__name__}: {str(e)}")
                        import traceback
                        traceback.print_exc()

                        result = {
                            'story_name': f"Lỗi: {type(e).__name__}",
                            'total_chapters': f"{str(e)[:50]}",
                            'domain': domain
                        }
                        self.finished.emit(result)
                        return

                    # Step 2: Navigate to story page
                    # If URL is a chapter URL, convert to story main page
                    # e.g., https://truyenphuongdong.com/read/dau-pha-thuong-khung/chuong-527
                    # -> https://truyenphuongdong.com/read/dau-pha-thuong-khung
                    url_to_fetch = self.url
                    if '/chuong-' in self.url or '/chapter-' in self.url:
                        import re
                        match = re.search(r'(https?://[^/]+/read/[^/]+)', self.url)
                        if match:
                            url_to_fetch = match.group(1)

                    # Navigate to story URL (now logged in)
                    driver.get(url_to_fetch)
                    time.sleep(5)  # Wait for JavaScript to load

                    # Scroll down to trigger lazy loading
                    try:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                        time.sleep(1)
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(1)
                    except:
                        pass

                    # Parse JSON metadata from page source
                    story_name = "Không tìm thấy tên truyện"
                    total_chapters = "N/A"

                    try:
                        page_source = driver.page_source
                        import json
                        import re

                        # Pattern 1: Look for escaped JSON in Next.js script blocks
                        # The JSON is embedded as: \"book\":{\"title\":\"...\",\"chapterNumber\":1641,...}
                        escaped_pattern = r'\\"book\\":\s*\{[^}]*\\"title\\":\s*\\"([^"\\\\]+)\\"[^}]*\\"chapterNumber\\":\s*(\d+)'
                        escaped_matches = re.search(escaped_pattern, page_source)

                        if escaped_matches:
                            story_name = escaped_matches.group(1)
                            total_chapters = escaped_matches.group(2)
                            print(f"✓ Found via escaped JSON: {story_name}, {total_chapters} chapters")
                        else:
                            # Pattern 2: Try unescaped JSON (for other sites)
                            json_pattern = r'"book":\s*\{[^}]*"title":\s*"([^"]+)"[^}]*"chapterNumber":\s*(\d+)'
                            json_matches = re.search(json_pattern, page_source)

                            if json_matches:
                                story_name = json_matches.group(1)
                                total_chapters = json_matches.group(2)
                                print(f"✓ Found via unescaped JSON: {story_name}, {total_chapters} chapters")

                        # Pattern 3: Fallback - search for any title and chapterNumber separately
                        if story_name == "Không tìm thấy tên truyện":
                            # Look for title field directly in page source
                            title_pattern = r'\\"title\\":\s*\\"([^"\\\\]+)\\"'
                            title_matches = re.findall(title_pattern, page_source)
                            if title_matches:
                                # Filter out generic titles and find the longest one (likely the story title)
                                valid_titles = [t for t in title_matches if len(t) > 5 and 'Đăng nhập' not in t and 'Login' not in t and 'reCAPTCHA' not in t]
                                if valid_titles:
                                    story_name = max(valid_titles, key=len)

                        # Pattern 4: Look for chapterNumber
                        if total_chapters == "N/A":
                            chapter_pattern = r'\\"chapterNumber\\":\s*(\d+)'
                            chapter_matches = re.findall(chapter_pattern, page_source)
                            if chapter_matches:
                                total_chapters = chapter_matches[0]

                    except Exception as e:
                        print(f"Error parsing JSON: {e}")

                    # Debug: Save page source if nothing found
                    if story_name == "Không tìm thấy tên truyện" or total_chapters == "N/A":
                        try:
                            debug_file = "truyenphuongdong_logged_in_debug.html"
                            with open(debug_file, 'w', encoding='utf-8') as f:
                                f.write(driver.page_source)
                            print(f"DEBUG: Logged in page source saved to {debug_file}")
                        except:
                            pass

                    result = {
                        'story_name': story_name,
                        'total_chapters': total_chapters,
                        'domain': domain
                    }
                    self.finished.emit(result)
                    return

                except Exception as e:
                    print(f"Outer exception: {type(e).__name__}: {str(e)}")
                    import traceback
                    traceback.print_exc()

                    error_msg = str(e)
                    if "symblos not available" in error_msg or "symbols" in error_msg.lower():
                        error_type = "ChromeDriver không tương thích"
                        suggestion = "Cập nhật Chrome hoặc ChromeDriver"
                    elif "chrome not found" in error_msg.lower():
                        error_type = "Chrome chưa cài đặt"
                        suggestion = "Cài Google Chrome"
                    elif "timeout" in error_msg.lower():
                        error_type = "Timeout khi tải trang"
                        suggestion = "Kiểm tra kết nối mạng"
                    else:
                        error_type = f"{type(e).__name__}"
                        suggestion = f"{str(e)[:60]}"

                    result = {
                        'story_name': error_type,
                        'total_chapters': suggestion,
                        'domain': domain
                    }
                    self.finished.emit(result)
                    return
                finally:
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass

            from bs4 import BeautifulSoup
            import requests

            # Get encoding
            encoding = self.config.get('encoding', 'utf-8')

            # Fetch main page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(self.url, headers=headers, timeout=10)

            # Handle encoding
            if encoding != 'utf-8':
                response.encoding = encoding

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract story info based on website
            story_name = "N/A"
            total_chapters = "N/A"

            # Piaotia.com
            if 'piaotia.com' in domain:
                # If URL is a chapter URL, extract story index URL
                # Chapter URL: https://www.piaotia.com/html/1/1767/11337659.html
                # Story index: https://www.piaotia.com/html/1/1767/
                import re
                match = re.search(r'(https?://[^/]+/html/\d+/\d+/)', self.url)
                if match:
                    story_index_url = match.group(1)
                    # Fetch story index page
                    response2 = requests.get(story_index_url, headers=headers, timeout=10)
                    response2.encoding = 'gbk'
                    soup = BeautifulSoup(response2.text, 'html.parser')

                # Story name from h1
                title_tag = soup.find('h1')
                if title_tag:
                    story_name = title_tag.get_text(strip=True)

                # Total chapters - find all chapter links
                # Try multiple selectors
                chapter_list = soup.find('ul', class_='centent') or soup.find('div', class_='centent')
                if chapter_list:
                    chapters = chapter_list.find_all('a')
                    total_chapters = str(len(chapters))
                else:
                    # Try alternative: find all links in body
                    all_links = soup.find_all('a', href=re.compile(r'/html/\d+/\d+/\d+\.html'))
                    if all_links:
                        total_chapters = str(len(all_links))

            # Default: try generic selectors
            else:
                title_tag = soup.find('h1') or soup.find('title')
                if title_tag:
                    story_name = title_tag.get_text(strip=True)

            result = {
                'story_name': story_name,
                'total_chapters': total_chapters,
                'domain': domain
            }

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(f"Lỗi khi lấy thông tin: {str(e)}")


class SPAScraperWorker(QThread):
    """Worker thread for scraping SPA websites (truyenphuongdong.com) using Selenium."""
    progress = pyqtSignal(str, int, int)  # message, current, total
    chapter_done = pyqtSignal(int, str, str)  # chapter_num, title, content
    finished = pyqtSignal(list)  # list of (chapter_num, title, content)
    error = pyqtSignal(str)

    def __init__(self, url: str, from_chapter: int, to_chapter: int, config: dict):
        super().__init__()
        self.url = url
        self.from_chapter = from_chapter
        self.to_chapter = to_chapter
        self.config = config
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        if not SELENIUM_AVAILABLE:
            self.error.emit("Selenium chưa được cài đặt. Vui lòng chạy: pip install selenium webdriver-manager")
            return

        # Import Selenium components
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # Try using undetected-chromedriver
        try:
            import undetected_chromedriver as uc
            USE_UNDETECTED = True
        except ImportError:
            USE_UNDETECTED = False
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager

        results = []
        driver = None

        try:
            print(f"SPAScraperWorker started: URL={self.url}, from={self.from_chapter}, to={self.to_chapter}")
            self.progress.emit("Đang khởi động trình duyệt...", 0, self.to_chapter - self.from_chapter + 1)

            # Initialize driver based on availability
            if USE_UNDETECTED:
                options = uc.ChromeOptions()
                options.add_argument("--headless=new")
                options.add_argument("--window-size=1920,1080")
                driver = uc.Chrome(options=options, use_subprocess=True)
            else:
                chrome_options = Options()
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--window-size=1920,1080")

                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.set_page_load_timeout(30)

            # Auto-login for truyenphuongdong.com
            if 'truyenphuongdong.com' in self.url:
                self.progress.emit("Đang đăng nhập...", 0, self.to_chapter - self.from_chapter + 1)

                # Get credentials
                username = db.get_setting('truyenphuongdong_username', '')
                password = db.get_setting('truyenphuongdong_password', '')

                if not username or not password:
                    self.error.emit("Cần cấu hình tài khoản đăng nhập trong Settings")
                    return

                # Login first
                try:
                    login_url = "https://truyenphuongdong.com/login"
                    driver.get(login_url)
                    time.sleep(3)

                    # Fill login form
                    email_field = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.NAME, "email"))
                    )
                    email_field.clear()
                    email_field.send_keys(username)

                    password_field = driver.find_element(By.NAME, "password")
                    password_field.clear()
                    password_field.send_keys(password)

                    # Submit
                    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    submit_btn.click()
                    time.sleep(5)

                    # Check login success
                    current_url = driver.current_url
                    if '/login' in current_url:
                        self.error.emit("Đăng nhập thất bại - kiểm tra username/password")
                        return

                except Exception as e:
                    self.error.emit(f"Lỗi đăng nhập: {str(e)}")
                    return

            # Navigate to story page
            self.progress.emit("Đang truy cập trang truyện...", 0, self.to_chapter - self.from_chapter + 1)
            print(f"Navigating to story page: {self.url}")
            driver.get(self.url)
            time.sleep(5)  # Wait for page to load
            print(f"Current URL after navigation: {driver.current_url}")
            print(f"Page title: {driver.title}")

            # Close "choose reading mode" overlay if exists
            try:
                print("Looking for reading mode overlay...")
                # Click on "SWIPE mode" button (first button) - contains text "vuốt sang trái"
                # IMPORTANT: Must use swipe mode to keep Swiper instance alive!
                swipe_mode_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'vuốt sang trái')]/ancestor::button"))
                )
                swipe_mode_btn.click()
                print("✓ Clicked SWIPE mode button to close overlay (keeps Swiper alive)")
                time.sleep(3)
            except Exception as e:
                print(f"✗ No overlay found or already closed: {e}")

            # Get current chapter info
            try:
                chapter_info = driver.find_element(By.CSS_SELECTOR, self.config.get("chapter_info_selector", "span.chapter-index"))
                chapter_text = chapter_info.text  # "Chương 527/535"
                current_chapter = int(re.search(r'(\d+)/', chapter_text).group(1))
                total_chapters = int(re.search(r'/(\d+)', chapter_text).group(1))
                print(f"✓ Found chapter info: {chapter_text} -> current={current_chapter}, total={total_chapters}")
            except Exception as e:
                current_chapter = 1
                total_chapters = 1000  # Default
                print(f"✗ Could not find chapter info: {e}. Using defaults: current={current_chapter}, total={total_chapters}")
            
            # For truyenphuongdong.com: Use chapter menu to navigate
            if 'truyenphuongdong.com' in self.url:
                # Navigate to the starting chapter using the chapter menu
                if self.from_chapter > 1:
                    print(f"Opening chapter menu to navigate to chapter {self.from_chapter}...")
                    try:
                        # Step 1: Find and click the menu button
                        print("Looking for menu button...")
                        menu_button = None
                        menu_selectors = [
                            'button[aria-label="menu"]',
                            'button[aria-label*="Menu"]',
                            'button.menu-button',
                            '[class*="menu"][role="button"]'
                        ]

                        for selector in menu_selectors:
                            try:
                                menu_button = driver.find_element(By.CSS_SELECTOR, selector)
                                if menu_button and menu_button.is_displayed():
                                    print(f"✓ Found menu button: {selector}")
                                    break
                            except:
                                continue

                        if menu_button:
                            menu_button.click()
                            print("✓ Clicked menu button")
                            time.sleep(2)  # Wait for menu to open

                            # Step 2: Find chapter list in the menu
                            print(f"Looking for chapter {self.from_chapter} in menu...")

                            # Try to find chapter by text
                            chapter_clicked = False
                            chapter_patterns = [
                                f"Chương {self.from_chapter}:",
                                f"Chương {self.from_chapter} ",
                                f"Chapter {self.from_chapter}",
                            ]

                            # Use JavaScript to find exact chapter match (avoid matching parent containers)
                            try:
                                result = driver.execute_script(f"""
                                    const patterns = {chapter_patterns};

                                    // Search within the menu for clickable chapter elements
                                    const menuElements = document.querySelectorAll('button, a, li, div[role="button"], div[role="menuitem"]');
                                    let found = null;

                                    for (const elem of menuElements) {{
                                        const text = elem.textContent.trim();
                                        for (const pattern of patterns) {{
                                            // Use startsWith for exact matching (not contains)
                                            if (text.startsWith(pattern)) {{
                                                found = elem;
                                                break;
                                            }}
                                        }}
                                        if (found) break;
                                    }}

                                    if (found) {{
                                        // Scroll menu container if needed
                                        const menuContainer = found.closest('[role="menu"]') || found.parentElement;
                                        if (menuContainer) {{
                                            const containerRect = menuContainer.getBoundingClientRect();
                                            const elemRect = found.getBoundingClientRect();
                                            if (elemRect.top < containerRect.top || elemRect.bottom > containerRect.bottom) {{
                                                found.scrollIntoView({{block: 'nearest', behavior: 'smooth'}});
                                            }}
                                        }}
                                        return found.textContent.trim();
                                    }}
                                    return null;
                                """)

                                if result:
                                    print(f"✓ Found chapter element: '{result}'")
                                    # Now click it using the same JavaScript context
                                    driver.execute_script(f"""
                                        const patterns = {chapter_patterns};
                                        const menuElements = document.querySelectorAll('button, a, li, div[role="button"], div[role="menuitem"]');

                                        for (const elem of menuElements) {{
                                            const text = elem.textContent.trim();
                                            for (const pattern of patterns) {{
                                                if (text.startsWith(pattern)) {{
                                                    elem.click();
                                                    return;
                                                }}
                                            }}
                                        }}
                                    """)
                                    chapter_clicked = True
                                    time.sleep(3)  # Wait for page to load
                                else:
                                    print(f"✗ Could not find chapter with patterns: {chapter_patterns}")
                            except Exception as e:
                                print(f"✗ Error finding chapter: {e}")

                            if chapter_clicked:
                                print("✓ Successfully navigated to chapter via menu")
                            else:
                                print("✗ Could not find chapter in menu, falling back to slideTo()")
                                raise Exception("Chapter not found in menu")
                        else:
                            print("✗ Menu button not found, falling back to slideTo()")
                            raise Exception("Menu button not found")

                    except Exception as e:
                        # Fallback: use slideTo()
                        print(f"Menu navigation failed: {e}. Using slideTo() fallback...")
                        try:
                            target_index = self.from_chapter - 1
                            result = driver.execute_script(f"""
                                const swiper = document.querySelector('.swiper').swiper;
                                if (swiper) {{
                                    swiper.slideTo({target_index}, 0);
                                    swiper.update();
                                    swiper.updateSlides();
                                    return swiper.activeIndex;
                                }}
                                return -1;
                            """)
                            print(f"✓ Jumped to index {result} using slideTo()")
                            time.sleep(3)
                        except Exception as e2:
                            print(f"✗ slideTo() also failed: {e2}")

                # Mark as SPA site that needs special handling
                self.is_truyenphuongdong = True
            elif current_chapter != self.from_chapter:
                # For other sites, try using chapter selector
                try:
                    # Click on chapter dropdown/selector
                    chapter_select = driver.find_element(By.CSS_SELECTOR, "select.chapter-select, .chapter-selector")
                    # Find and click the target chapter option
                    for option in chapter_select.find_elements(By.TAG_NAME, "option"):
                        if f"Chương {self.from_chapter}" in option.text:
                            option.click()
                            time.sleep(2)
                            break
                except:
                    # Navigate using next/prev buttons
                    while current_chapter < self.from_chapter and not self.is_cancelled:
                        try:
                            next_btn = driver.find_element(By.CSS_SELECTOR, self.config.get("next_btn_selector", "a.next-chap"))
                            next_btn.click()
                            time.sleep(1)
                            current_chapter += 1
                        except:
                            break
            
            # Start scraping chapters
            total = self.to_chapter - self.from_chapter + 1
            
            for i, chapter_num in enumerate(range(self.from_chapter, self.to_chapter + 1)):
                if self.is_cancelled:
                    break

                retry_count = 0
                max_retries = 3
                success = False

                while retry_count < max_retries and not success:
                    try:
                        self.progress.emit(f"Đang lấy chương {chapter_num}...", i + 1, total)
                        print(f"=== Scraping chapter {chapter_num} ===")
                        print(f"Current URL: {driver.current_url}")

                        # For truyenphuongdong.com: Navigate via menu for EACH chapter
                        if hasattr(self, 'is_truyenphuongdong') and self.is_truyenphuongdong and chapter_num > self.from_chapter:
                            print(f"Navigating to chapter {chapter_num} via menu...")
                            try:
                                # Step 1: Close any open modals/backdrops first
                                try:
                                    print("Closing any open modals...")
                                    driver.execute_script("""
                                        const backdrops = document.querySelectorAll('.MuiBackdrop-root, .MuiModal-backdrop');
                                        backdrops.forEach(b => b.click());
                                    """)
                                    time.sleep(0.5)
                                except:
                                    pass

                                # Step 2: Click menu button (wait until clickable)
                                menu_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="menu"]'))
                                )
                                menu_button.click()
                                print("✓ Menu opened")
                                time.sleep(1.5)

                                # Step 3: DEBUG - Get all chapter texts in menu
                                available_chapters = driver.execute_script("""
                                    const elements = Array.from(document.querySelectorAll('*'));
                                    const chapters = [];
                                    elements.forEach(el => {
                                        const text = el.textContent;
                                        if (text && text.match(/Chương \\d+/)) {
                                            chapters.push(text.trim().substring(0, 60));
                                        }
                                    });
                                    return [...new Set(chapters)].slice(0, 15);
                                """)
                                print(f"DEBUG: Found {len(available_chapters)} chapter texts:")
                                for ch_text in available_chapters[:10]:
                                    print(f"  - {ch_text}")

                                # Step 4: Find and click chapter using JavaScript for exact matching
                                chapter_clicked = False
                                chapter_patterns = [
                                    f"Chương {chapter_num}:",
                                    f"Chương {chapter_num} ",
                                    f"Chương {chapter_num}\n",
                                ]

                                try:
                                    # Use JavaScript to find exact chapter match (avoid matching parent containers)
                                    result = driver.execute_script(f"""
                                        const patterns = {chapter_patterns};

                                        // Search within the menu for clickable chapter elements
                                        const menuElements = document.querySelectorAll('button, a, li, div[role="button"], div[role="menuitem"]');
                                        let found = null;

                                        for (const elem of menuElements) {{
                                            const text = elem.textContent.trim();
                                            for (const pattern of patterns) {{
                                                // Use startsWith for exact matching (not contains)
                                                if (text.startsWith(pattern)) {{
                                                    found = elem;
                                                    break;
                                                }}
                                            }}
                                            if (found) break;
                                        }}

                                        if (found) {{
                                            // Scroll menu container if needed
                                            const menuContainer = found.closest('[role="menu"]') || found.parentElement;
                                            if (menuContainer) {{
                                                const containerRect = menuContainer.getBoundingClientRect();
                                                const elemRect = found.getBoundingClientRect();
                                                if (elemRect.top < containerRect.top || elemRect.bottom > containerRect.bottom) {{
                                                    found.scrollIntoView({{block: 'nearest', behavior: 'smooth'}});
                                                }}
                                            }}
                                            return found.textContent.trim();
                                        }}
                                        return null;
                                    """)

                                    if result:
                                        print(f"✓ Found chapter element: '{result}'")
                                        # Wait a moment for scroll animation
                                        time.sleep(0.3)
                                        # Now click it using the same JavaScript context
                                        driver.execute_script(f"""
                                            const patterns = {chapter_patterns};
                                            const menuElements = document.querySelectorAll('button, a, li, div[role="button"], div[role="menuitem"]');

                                            for (const elem of menuElements) {{
                                                const text = elem.textContent.trim();
                                                for (const pattern of patterns) {{
                                                    if (text.startsWith(pattern)) {{
                                                        elem.click();
                                                        return;
                                                    }}
                                                }}
                                            }}
                                        """)
                                        chapter_clicked = True
                                        print(f"✓ Clicked chapter {chapter_num}")
                                        time.sleep(3)  # Wait for content to load
                                    else:
                                        print(f"✗ Could not find chapter {chapter_num} with patterns: {chapter_patterns}")
                                except Exception as e:
                                    print(f"✗ Error finding chapter {chapter_num}: {e}")

                                if not chapter_clicked:
                                    print(f"✗ Could not navigate to chapter {chapter_num}")

                                # Step 5: Close menu
                                try:
                                    driver.execute_script("""
                                        const backdrops = document.querySelectorAll('.MuiBackdrop-root');
                                        backdrops.forEach(b => b.click());
                                    """)
                                    print("✓ Menu closed")
                                except:
                                    pass

                            except Exception as e:
                                print(f"✗ Menu navigation failed: {e}")
                                # Ensure menu is closed
                                try:
                                    driver.execute_script("""
                                        const backdrops = document.querySelectorAll('.MuiBackdrop-root');
                                        backdrops.forEach(b => b.click());
                                    """)
                                except:
                                    pass

                        # Wait for content to load (shorter for SPA sites)
                        if hasattr(self, 'is_truyenphuongdong') and self.is_truyenphuongdong:
                            time.sleep(0.5)  # Menu already waited 2s
                        else:
                            time.sleep(2)

                        # Get title - MUST use .swiper-slide-active for truyenphuongdong.com
                        title = None
                        title_selectors = [
                            ".swiper-slide-active div.text-center.font-bold",  # truyenphuongdong.com - active slide only!
                            "h2.chapter-title",
                            "h1.chapter-title",
                            ".chapter-title",
                            "div.text-center.font-bold",  # fallback (may get wrong chapter)
                            "h1",
                            "h2"
                        ]
                        for selector in title_selectors:
                            try:
                                title_elem = driver.find_element(By.CSS_SELECTOR, selector)
                                title = title_elem.text.strip()
                                if title and len(title) > 3 and 'Vui lòng' not in title and 'chọn cách' not in title:
                                    print(f"✓ Found title via '{selector}': {title[:50]}")
                                    break
                            except:
                                continue

                        if not title:
                            title = f"Chương {chapter_num}"
                            print(f"✗ No title found, using default: {title}")

                        # Get content - MUST use .swiper-slide-active for truyenphuongdong.com
                        content = None
                        content_selectors = [
                            ".swiper-slide-active div.whitespace-pre-line",  # truyenphuongdong.com - active slide only!
                            ".swiper-slide-active div[class*='space-y']",
                            "div.chapter-content",
                            ".chapter-content",
                            "div.content",
                            ".content",
                            "div.whitespace-pre-line",  # fallback (may get wrong chapter)
                            "article"
                        ]
                        for selector in content_selectors:
                            try:
                                content_elem = driver.find_element(By.CSS_SELECTOR, selector)
                                content_text = content_elem.text.strip()
                                if content_text and len(content_text) > 100:
                                    content = content_text
                                    print(f"✓ Found content via '{selector}': {len(content)} chars")
                                    break
                            except:
                                continue

                        if not content:
                            print(f"✗ No content found with any selector")
                            # Save debug HTML
                            with open('truyenphuongdong_chapter_debug.html', 'w', encoding='utf-8') as f:
                                f.write(driver.page_source)
                            print(f"Debug HTML saved to truyenphuongdong_chapter_debug.html")
                            raise Exception("Không tìm thấy nội dung")

                        # Extract real chapter number from title for accurate filename
                        real_chapter_num = extract_chapter_number(title)
                        if real_chapter_num == 0:
                            real_chapter_num = chapter_num

                        # Store with real chapter number
                        results.append((real_chapter_num, title, content))
                        self.chapter_done.emit(real_chapter_num, title, content)
                        success = True
                        print(f"✓ Successfully scraped chapter {chapter_num}: {title[:30]}")

                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            self.progress.emit(f"Lỗi chương {chapter_num}, thử lại ({retry_count}/{max_retries})...", i + 1, total)
                            time.sleep(2)
                        else:
                            self.progress.emit(f"Bỏ qua chương {chapter_num} (lỗi: {str(e)[:50]})", i + 1, total)

                # Navigate to next chapter (if not last)
                # NOTE: For truyenphuongdong.com, navigation is done via menu before scraping each chapter
                if chapter_num < self.to_chapter and not self.is_cancelled:
                    if not (hasattr(self, 'is_truyenphuongdong') and self.is_truyenphuongdong):
                        # Other sites: use traditional navigation
                        try:
                            next_btn = driver.find_element(By.CSS_SELECTOR, self.config.get("next_btn_selector", "a.next-chap"))
                            next_btn.click()
                            time.sleep(2)
                        except Exception as e:
                            print(f"Error navigating: {e}")
                            break
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Lỗi: {str(e)}")
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass


class StaticScraperWorker(QThread):
    """Worker thread for scraping static HTML websites."""
    progress = pyqtSignal(str, int, int)  # message, current, total
    chapter_done = pyqtSignal(int, str, str)  # chapter_num, title, content
    finished = pyqtSignal(list)  # list of (chapter_num, title, content)
    error = pyqtSignal(str)
    
    def __init__(self, urls: list, config: dict):
        super().__init__()
        self.urls = urls  # List of (chapter_num, url)
        self.config = config
        self.is_cancelled = False
    
    def cancel(self):
        self.is_cancelled = True
    
    def run(self):
        if not BS4_AVAILABLE:
            self.error.emit("BeautifulSoup chưa được cài đặt. Vui lòng chạy: pip install beautifulsoup4")
            return
        
        results = []
        total = len(self.urls)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for i, (chapter_num, url) in enumerate(self.urls):
            if self.is_cancelled:
                break
            
            retry_count = 0
            max_retries = 3
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    self.progress.emit(f"Đang lấy chương {chapter_num}...", i + 1, total)
                    
                    # Get encoding
                    encoding = self.config.get("encoding", "utf-8")
                    
                    # Fetch page
                    response = requests.get(url, headers=headers, timeout=15)
                    response.encoding = encoding
                    
                    # Parse HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Get title
                    try:
                        title_elem = soup.select_one(self.config.get("title_selector", "h1"))
                        title = title_elem.get_text(strip=True) if title_elem else f"Chương {chapter_num}"
                    except:
                        title = f"Chương {chapter_num}"
                    
                    # Get content - handle special parsers
                    special_parser = self.config.get("special_parser", None)

                    if special_parser == "piaotia":
                        # Piaotia.com: Content is text between last </table> and <div id="Commenddiv">
                        # Use regex because BeautifulSoup has issues with this site's structure
                        import re
                        import html as html_module
                        html_text = response.text

                        # Extract content between markers
                        pattern = r'</table>(.*?)<div id="Commenddiv"'
                        content_match = re.search(pattern, html_text, re.DOTALL)

                        if content_match:
                            content_html = content_match.group(1)

                            # Remove unwanted tags
                            content_html = re.sub(r'<script[^>]*>.*?</script>', '', content_html, flags=re.DOTALL)
                            content_html = re.sub(r'<div[^>]*>.*?</div>', '', content_html, flags=re.DOTALL)
                            content_html = re.sub(r'<a[^>]*>.*?</a>', '', content_html, flags=re.DOTALL)
                            content_html = re.sub(r'<center[^>]*>.*?</center>', '', content_html, flags=re.DOTALL)

                            # Replace br with newline
                            content_html = re.sub(r'<br\s*/?>', '\n', content_html)

                            # Remove all remaining tags
                            content = re.sub(r'<[^>]+>', '', content_html)

                            # Decode HTML entities (&nbsp; &amp; etc.)
                            content = html_module.unescape(content)

                            # Remove non-breaking spaces
                            content = content.replace('\xa0', '')  # Unicode non-breaking space

                            # Clean whitespace
                            lines = [line.strip() for line in content.split('\n') if line.strip() and len(line.strip()) > 2]
                            content = '\n'.join(lines)
                        else:
                            raise Exception("Không tìm thấy content pattern")
                    else:
                        # Normal content extraction
                        content_elem = soup.select_one(self.config.get("content_selector", "#content"))
                        if content_elem:
                            # Remove ads, scripts, etc.
                            for tag in content_elem.find_all(['script', 'style', 'ins', 'iframe']):
                                tag.decompose()

                            content = content_elem.get_text(separator='\n', strip=True)
                        else:
                            raise Exception("Không tìm thấy nội dung")

                    # Validate content
                    if content and len(content) > 100:
                        results.append((chapter_num, title, content))
                        self.chapter_done.emit(chapter_num, title, content)
                        success = True
                    else:
                        raise Exception(f"Nội dung quá ngắn ({len(content)} chars)")
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        self.progress.emit(f"Lỗi chương {chapter_num}, thử lại ({retry_count}/{max_retries})...", i + 1, total)
                        time.sleep(1)
                    else:
                        self.progress.emit(f"Bỏ qua chương {chapter_num} (lỗi: {str(e)[:50]})", i + 1, total)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        self.finished.emit(results)


class ClaudeProcessWorker(QThread):
    """Worker thread for processing content with Claude."""
    progress = pyqtSignal(str, int, int)
    chapter_done = pyqtSignal(int, str, str)  # chapter_num, title, processed_content
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, chapters: list, instructions: str, memory: str, glossary: str,
                 model: str = None, extended_thinking: bool = True):
        super().__init__()
        self.chapters = chapters  # List of (chapter_num, title, content)
        self.instructions = instructions
        self.memory = memory
        self.glossary = glossary
        self.model = model
        self.extended_thinking = extended_thinking
        self.is_cancelled = False
    
    def cancel(self):
        self.is_cancelled = True
    
    def run(self):
        results = []
        total = len(self.chapters)

        # Apply project-specific model and thinking settings
        if self.model:
            claude_client.set_model(self.model)
        claude_client.set_extended_thinking(self.extended_thinking, claude_client.thinking_budget)

        # Build system prompt
        system_parts = []
        
        if self.instructions:
            system_parts.append(self.instructions)
        
        if self.glossary:
            system_parts.append(f"\n## Thuật ngữ cần tuân thủ:\n{self.glossary}")
        
        if self.memory:
            system_parts.append(f"\n## Thông tin bổ sung:\n{self.memory}")
        
        system_prompt = "\n\n".join(system_parts) if system_parts else ""
        
        for i, (chapter_num, title, content) in enumerate(self.chapters):
            if self.is_cancelled:
                break
            
            try:
                self.progress.emit(f"Claude đang xử lý: {title}...", i + 1, total)
                
                # Build message
                messages = [
                    {
                        "role": "user",
                        "content": f"Hãy biên tập nội dung chương truyện sau theo hướng dẫn:\n\n**{title}**\n\n{content}"
                    }
                ]
                
                # Get response
                full_response = ""
                for chunk in claude_client.stream_message(messages, system_prompt):
                    full_response += chunk
                    if self.is_cancelled:
                        break
                
                if full_response:
                    results.append((chapter_num, title, full_response))
                    self.chapter_done.emit(chapter_num, title, full_response)
                
            except Exception as e:
                self.progress.emit(f"Lỗi Claude chương {chapter_num}: {str(e)[:50]}", i + 1, total)
                # Keep original content if Claude fails
                results.append((chapter_num, title, content))
        
        self.finished.emit(results)


class BatchProcessWorker(QThread):
    """Worker thread for batch processing content with Claude."""
    progress = pyqtSignal(str, int, int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, chapters: list, instructions: str, memory: str, glossary: str,
                 model: str = None, extended_thinking: bool = True):
        super().__init__()
        self.chapters = chapters  # List of (chapter_num, title, content)
        self.instructions = instructions
        self.memory = memory
        self.glossary = glossary
        self.model = model
        self.extended_thinking = extended_thinking
        self.is_cancelled = False
        self.batch_id = None

    def cancel(self):
        self.is_cancelled = True
        # Cancel batch if it exists
        if self.batch_id:
            try:
                claude_client.cancel_batch(self.batch_id)
            except:
                pass

    def run(self):
        import time

        try:
            # Apply project-specific model and thinking settings
            if self.model:
                claude_client.set_model(self.model)
            claude_client.set_extended_thinking(self.extended_thinking, claude_client.thinking_budget)

            # Build system prompt
            system_parts = []

            if self.instructions:
                system_parts.append(self.instructions)

            if self.glossary:
                system_parts.append(f"\n## Thuật ngữ cần tuân thủ:\n{self.glossary}")

            if self.memory:
                system_parts.append(f"\n## Thông tin bổ sung:\n{self.memory}")

            system_prompt = "\n\n".join(system_parts) if system_parts else ""

            # Build batch requests
            self.progress.emit("Đang chuẩn bị batch requests...", 0, len(self.chapters))

            batch_requests = []
            for chapter_num, title, content in self.chapters:
                custom_id = f"chapter_{chapter_num}"
                user_content = f"Hãy biên tập nội dung chương truyện sau theo hướng dẫn:\n\n**{title}**\n\n{content}"

                request = claude_client.build_batch_request(
                    custom_id=custom_id,
                    content=user_content,
                    system_prompt=system_prompt
                )
                batch_requests.append(request)

            if self.is_cancelled:
                return

            # Create batch
            self.progress.emit("Đang gửi batch lên server...", 0, len(self.chapters))
            batch_info = claude_client.create_batch(batch_requests)
            self.batch_id = batch_info['id']

            self.progress.emit(f"Batch đã tạo (ID: {self.batch_id[:8]}...). Đang xử lý...", 0, len(self.chapters))

            # Poll for completion
            while not self.is_cancelled:
                time.sleep(10)  # Poll every 10 seconds

                status_info = claude_client.get_batch_status(self.batch_id)
                status = status_info['status']
                counts = status_info['request_counts']

                succeeded = counts.get('succeeded', 0)
                errored = counts.get('errored', 0)
                processing = counts.get('processing', 0)

                self.progress.emit(
                    f"Batch đang xử lý... (Hoàn thành: {succeeded}/{len(self.chapters)}, Lỗi: {errored})",
                    succeeded,
                    len(self.chapters)
                )

                if status == 'ended':
                    break

            if self.is_cancelled:
                return

            # Get results
            self.progress.emit("Đang lấy kết quả...", len(self.chapters), len(self.chapters))
            batch_results = claude_client.get_batch_results(self.batch_id)

            # Map results back to chapters
            results_map = {r['custom_id']: r for r in batch_results}
            final_results = []

            for chapter_num, title, original_content in self.chapters:
                custom_id = f"chapter_{chapter_num}"
                result = results_map.get(custom_id)

                if result and result['type'] == 'succeeded':
                    processed_content = result['content']
                    final_results.append((chapter_num, title, processed_content))
                else:
                    # Keep original if processing failed
                    error_msg = result.get('error', 'Unknown error') if result else 'No result'
                    self.progress.emit(f"Lỗi chương {chapter_num}: {error_msg}", 0, 0)
                    final_results.append((chapter_num, title, original_content))

            self.finished.emit(final_results)

        except Exception as e:
            self.error.emit(f"Lỗi batch processing: {str(e)}")


class LinkToTextWidget(QWidget):
    """Link to Text conversion widget."""
    
    def __init__(self):
        super().__init__()
        self.project_id = None
        self.scraper_worker = None
        self.claude_worker = None
        self.batch_worker = None
        self.scraped_chapters = []
        self.processed_chapters = []
        self.detected_config = None

        self.setup_ui()
        self.check_dependencies()
    
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area for all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['bg_dark']};
            }}
        """)

        # Content widget inside scroll
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()

        title = QLabel("🔗 Link to Text")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(title)

        header.addStretch()

        # Dependency status
        self.dep_status = QLabel("")
        self.dep_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        header.addWidget(self.dep_status)

        layout.addLayout(header)
        
        # Source section
        source_group = QGroupBox("📥 Nguồn truyện")
        source_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """)
        source_layout = QVBoxLayout(source_group)
        source_layout.setSpacing(12)
        
        # URL input label
        url_label_row = QHBoxLayout()
        url_label = QLabel("🔗 Link truyện (mỗi link một dòng):")
        url_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 500;")
        url_label_row.addWidget(url_label)
        url_label_row.addStretch()
        source_layout.addLayout(url_label_row)

        # URL input area
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("https://truyenphuongdong.com/read/ten-truyen\nhttps://piaotia.com/html/1/1767/11360742.html\n...")
        self.url_input.setMaximumHeight(120)
        self.url_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 12px;
                color: {COLORS['text_primary']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }}
            QTextEdit:focus {{
                border-color: {COLORS['accent']};
            }}
        """)
        self.url_input.textChanged.connect(self.on_url_changed)
        source_layout.addWidget(self.url_input)

        # Buttons row
        url_buttons_row = QHBoxLayout()

        paste_btn = QPushButton("📋 Dán")
        paste_btn.setToolTip("Dán từ clipboard")
        paste_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        paste_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        paste_btn.clicked.connect(self.paste_url)
        url_buttons_row.addWidget(paste_btn)

        upload_file_btn = QPushButton("📄 Tải file .txt")
        upload_file_btn.setToolTip("Tải file txt chứa danh sách link")
        upload_file_btn.setStyleSheet(paste_btn.styleSheet())
        upload_file_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        upload_file_btn.clicked.connect(self.upload_link_file_main)
        url_buttons_row.addWidget(upload_file_btn)

        url_buttons_row.addStretch()

        detect_btn = QPushButton("🔍 Kiểm tra")
        detect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        detect_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        detect_btn.clicked.connect(self.detect_website)
        url_buttons_row.addWidget(detect_btn)

        source_layout.addLayout(url_buttons_row)
        
        # Supported websites
        websites_label = QLabel("Website hỗ trợ: " + " ".join([f"✅ {domain}" for domain in SUPPORTED_WEBSITES.keys()]))
        websites_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        websites_label.setWordWrap(True)
        source_layout.addWidget(websites_label)
        
        # Website info (shown after detection)
        self.website_info_frame = QFrame()
        self.website_info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
                padding: 12px 16px;
            }}
        """)
        self.website_info_frame.setVisible(False)
        info_layout = QVBoxLayout(self.website_info_frame)
        info_layout.setContentsMargins(0, 8, 0, 8)
        info_layout.setSpacing(8)

        # Title
        info_title = QLabel("ℹ️ Thông tin truyện")
        info_title.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 4px;
        """)
        info_layout.addWidget(info_title)

        # Website row
        website_row = QHBoxLayout()
        website_row.setSpacing(8)
        website_title = QLabel("🌐 Website:")
        website_title.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 13px;
            font-weight: 600;
            min-width: 120px;
        """)
        website_row.addWidget(website_title)

        self.website_label = QLabel("")
        self.website_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 13px;
        """)
        self.website_label.setWordWrap(True)
        website_row.addWidget(self.website_label, 1)
        info_layout.addLayout(website_row)

        # Story name row
        story_row = QHBoxLayout()
        story_row.setSpacing(8)
        story_title = QLabel("📖 Tên truyện:")
        story_title.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 13px;
            font-weight: 600;
            min-width: 120px;
        """)
        story_row.addWidget(story_title)

        self.story_name_label = QLabel("")
        self.story_name_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 13px;
        """)
        self.story_name_label.setWordWrap(True)
        story_row.addWidget(self.story_name_label, 1)
        info_layout.addLayout(story_row)

        # Total chapters row
        chapters_row = QHBoxLayout()
        chapters_row.setSpacing(8)
        chapters_title = QLabel("📚 Tổng chương:")
        chapters_title.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 13px;
            font-weight: 600;
            min-width: 120px;
        """)
        chapters_row.addWidget(chapters_title)

        self.total_chapters_label = QLabel("")
        self.total_chapters_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 13px;
        """)
        self.total_chapters_label.setWordWrap(True)
        chapters_row.addWidget(self.total_chapters_label, 1)
        info_layout.addLayout(chapters_row)

        # Loading indicator
        self.info_loading_label = QLabel("⏳ Đang tải thông tin...")
        self.info_loading_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            font-style: italic;
            padding: 4px 0px;
        """)
        self.info_loading_label.setVisible(False)
        info_layout.addWidget(self.info_loading_label)

        source_layout.addWidget(self.website_info_frame)
        
        # Multi-link input (for static websites)
        self.multi_link_frame = QFrame()
        self.multi_link_frame.setVisible(False)
        multi_layout = QVBoxLayout(self.multi_link_frame)
        multi_layout.setContentsMargins(0, 8, 0, 0)
        
        multi_label = QLabel("📝 Hoặc dán nhiều link (mỗi link 1 dòng):")
        multi_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        multi_layout.addWidget(multi_label)
        
        self.multi_link_input = QTextEdit()
        self.multi_link_input.setPlaceholderText("https://piaotia.com/html/1/1767/11360742.html\nhttps://piaotia.com/html/1/1767/11360743.html\n...")
        self.multi_link_input.setMaximumHeight(100)
        self.multi_link_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px;
                color: {COLORS['text_primary']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }}
        """)
        multi_layout.addWidget(self.multi_link_input)
        
        # Upload file button
        upload_row = QHBoxLayout()
        upload_row.addStretch()
        upload_btn = QPushButton("📄 Tải file .txt chứa link")
        upload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        upload_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        upload_btn.clicked.connect(self.upload_link_file)
        upload_row.addWidget(upload_btn)
        multi_layout.addLayout(upload_row)
        
        source_layout.addWidget(self.multi_link_frame)
        
        # Chapter range (for SPA websites)
        self.chapter_range_frame = QFrame()
        self.chapter_range_frame.setVisible(False)
        range_layout = QHBoxLayout(self.chapter_range_frame)
        range_layout.setContentsMargins(0, 8, 0, 0)
        
        range_label = QLabel("📖 Phạm vi chương:")
        range_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        range_layout.addWidget(range_label)
        
        from_label = QLabel("Từ:")
        from_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        range_layout.addWidget(from_label)
        
        self.from_chapter_spin = QSpinBox()
        self.from_chapter_spin.setMinimum(1)
        self.from_chapter_spin.setMaximum(10000)
        self.from_chapter_spin.setValue(1)
        self.from_chapter_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                color: {COLORS['text_primary']};
                min-width: 80px;
            }}
        """)
        range_layout.addWidget(self.from_chapter_spin)
        
        to_label = QLabel("Đến:")
        to_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        range_layout.addWidget(to_label)
        
        self.to_chapter_spin = QSpinBox()
        self.to_chapter_spin.setMinimum(1)
        self.to_chapter_spin.setMaximum(10000)
        self.to_chapter_spin.setValue(10)
        self.to_chapter_spin.setStyleSheet(self.from_chapter_spin.styleSheet())
        range_layout.addWidget(self.to_chapter_spin)
        
        range_layout.addStretch()
        
        source_layout.addWidget(self.chapter_range_frame)
        
        layout.addWidget(source_group)
        
        # Settings section
        settings_row = QHBoxLayout()
        settings_row.setSpacing(16)
        
        # Processing level
        level_group = QGroupBox("🎯 Mức độ xử lý")
        level_group.setStyleSheet(source_group.styleSheet())
        level_layout = QVBoxLayout(level_group)
        
        self.level_group = QButtonGroup(self)

        # Style for radio buttons
        radio_style = f"""
            QRadioButton {{
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-weight: 500;
                padding: 4px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {COLORS['border_light']};
                background-color: {COLORS['bg_light']};
            }}
            QRadioButton::indicator:hover {{
                border-color: {COLORS['accent']};
            }}
            QRadioButton::indicator:checked {{
                background-color: {COLORS['accent']};
                border-color: {COLORS['accent']};
            }}
        """

        self.level_scrape = QRadioButton("Chỉ lấy nội dung (miễn phí)")
        self.level_scrape.setStyleSheet(radio_style)
        self.level_scrape.setChecked(True)
        self.level_group.addButton(self.level_scrape, 0)
        level_layout.addWidget(self.level_scrape)

        scrape_desc = QLabel("→ Lấy text từ website → Xuất file TXT")
        scrape_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; margin-left: 28px;")
        level_layout.addWidget(scrape_desc)

        self.level_claude = QRadioButton("Lấy + Biên tập bằng Claude (realtime)")
        self.level_claude.setStyleSheet(radio_style)
        self.level_group.addButton(self.level_claude, 1)
        level_layout.addWidget(self.level_claude)

        claude_desc = QLabel("→ Lấy text → Claude biên tập ngay (xem kết quả realtime)")
        claude_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; margin-left: 28px;")
        level_layout.addWidget(claude_desc)

        self.level_batch = QRadioButton("Lấy + Biên tập bằng Claude (batch - rẻ hơn 50%)")
        self.level_batch.setStyleSheet(radio_style)
        self.level_group.addButton(self.level_batch, 2)
        level_layout.addWidget(self.level_batch)

        batch_desc = QLabel("→ Lấy text → Gửi batch → Đợi vài phút → Nhận kết quả")
        batch_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; margin-left: 28px;")
        level_layout.addWidget(batch_desc)

        settings_row.addWidget(level_group, 1)
        
        # Output options
        output_group = QGroupBox("📤 Kết quả xuất ra")
        output_group.setStyleSheet(source_group.styleSheet())
        output_layout = QVBoxLayout(output_group)

        self.output_separate = QRadioButton("Mỗi chương → 1 file riêng")
        self.output_separate.setStyleSheet(radio_style)
        self.output_separate.setChecked(True)
        output_layout.addWidget(self.output_separate)

        separate_desc = QLabel("→ chuong-001.txt, chuong-002.txt, ...")
        separate_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; margin-left: 28px;")
        output_layout.addWidget(separate_desc)

        self.output_merged = QRadioButton("Gộp tất cả → 1 file")
        self.output_merged.setStyleSheet(radio_style)
        output_layout.addWidget(self.output_merged)

        merged_desc = QLabel("→ ten-truyen_c1-100.txt")
        merged_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; margin-left: 28px;")
        output_layout.addWidget(merged_desc)
        
        settings_row.addWidget(output_group, 1)
        
        layout.addLayout(settings_row)
        
        # Start button
        self.start_btn = QPushButton("🚀 Bắt đầu lấy nội dung")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.start_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.start_btn.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_btn)
        
        # Progress
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 8px;
            }}
        """)
        self.progress_frame.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(16, 12, 16, 12)
        
        progress_header = QHBoxLayout()
        self.progress_label = QLabel("Đang xử lý...")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        progress_header.addWidget(self.progress_label)
        progress_header.addStretch()
        self.progress_count = QLabel("0/0")
        self.progress_count.setStyleSheet(f"color: {COLORS['accent']}; font-weight: 600;")
        progress_header.addWidget(self.progress_count)
        progress_layout.addLayout(progress_header)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {COLORS['bg_lighter']};
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 4px;
            }}
        """)
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        # Cancel button
        cancel_btn_layout = QHBoxLayout()
        cancel_btn_layout.addStretch()
        self.cancel_btn = QPushButton("⏹️ Dừng")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #dc2626;
            }}
        """)
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.clicked.connect(self.cancel_scraping)
        cancel_btn_layout.addWidget(self.cancel_btn)
        progress_layout.addLayout(cancel_btn_layout)
        
        layout.addWidget(self.progress_frame)
        
        # Results section
        results_label = QLabel("📄 Kết quả")
        results_label.setStyleSheet(f"font-weight: 600; color: {COLORS['text_secondary']};")
        layout.addWidget(results_label)
        
        # Results list
        self.results_frame = QFrame()
        self.results_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 8px;
            }}
        """)
        results_inner_layout = QVBoxLayout(self.results_frame)
        results_inner_layout.setContentsMargins(12, 12, 12, 12)
        
        self.results_list = QTextEdit()
        self.results_list.setReadOnly(True)
        self.results_list.setPlaceholderText("Kết quả sẽ hiển thị ở đây...")
        self.results_list.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px;
                color: {COLORS['text_primary']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }}
        """)
        self.results_list.setMaximumHeight(150)
        results_inner_layout.addWidget(self.results_list)
        
        layout.addWidget(self.results_frame)
        
        # Action buttons
        actions_row = QHBoxLayout()
        
        self.add_to_files_check = QCheckBox("📁 Thêm vào Files của Project")
        self.add_to_files_check.setStyleSheet(f"color: {COLORS['text_primary']};")
        actions_row.addWidget(self.add_to_files_check)
        
        actions_row.addStretch()
        
        self.save_btn = QPushButton("💾 Lưu kết quả")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #16a34a;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.clicked.connect(self.save_results)
        self.save_btn.setEnabled(False)
        actions_row.addWidget(self.save_btn)
        
        layout.addLayout(actions_row)

        # Add stretch at bottom
        layout.addStretch()

        # Set content widget to scroll area
        scroll.setWidget(content_widget)

        # Add scroll area to main layout
        main_layout.addWidget(scroll)

    def check_dependencies(self):
        """Check if required dependencies are installed."""
        missing = []
        
        if not SELENIUM_AVAILABLE:
            missing.append("selenium + webdriver-manager")
        
        if not BS4_AVAILABLE:
            missing.append("beautifulsoup4")
        
        if missing:
            self.dep_status.setText(f"⚠️ Thiếu: {', '.join(missing)}")
            self.dep_status.setStyleSheet(f"color: {COLORS['warning']}; font-size: 11px;")
        else:
            self.dep_status.setText("✅ Sẵn sàng")
            self.dep_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px;")
    
    def set_project(self, project_id: int):
        """Set current project."""
        self.project_id = project_id
    
    def paste_url(self):
        """Paste URL from clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        self.url_input.setPlainText(clipboard.text())

    def upload_link_file_main(self):
        """Upload a text file containing links to main input."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file chứa link",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.url_input.setPlainText(content.strip())
                QMessageBox.information(self, "Thành công", f"Đã tải {len(content.strip().splitlines())} link từ file!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể đọc file:\n{str(e)}")

    def on_url_changed(self):
        """Handle URL input change."""
        # Reset UI
        self.website_info_frame.setVisible(False)
        self.chapter_range_frame.setVisible(False)
        self.multi_link_frame.setVisible(False)
        self.detected_config = None
    
    def detect_website(self):
        """Detect website type from URL."""
        urls_text = self.url_input.toPlainText().strip()

        if not urls_text:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập link truyện")
            return

        # Get first URL to detect website type
        url = urls_text.split('\n')[0].strip()

        config = detect_website(url)

        if not config:
            QMessageBox.warning(
                self,
                "Không hỗ trợ",
                f"Website này chưa được hỗ trợ.\n\nCác website được hỗ trợ:\n• " +
                "\n• ".join(SUPPORTED_WEBSITES.keys())
            )
            return

        self.detected_config = config

        # Show website info frame
        self.website_info_frame.setVisible(True)
        self.info_loading_label.setVisible(True)
        self.website_label.setText(config['domain'])
        self.story_name_label.setText("...")
        self.total_chapters_label.setText("...")

        # Show/hide additional options based on type
        if config['type'] == 'spa':
            self.chapter_range_frame.setVisible(True)
            self.multi_link_frame.setVisible(False)
        else:
            self.chapter_range_frame.setVisible(False)
            self.multi_link_frame.setVisible(True)

        # Fetch story info in background
        self.info_worker = StoryInfoWorker(url, config)
        self.info_worker.finished.connect(self.on_story_info_loaded)
        self.info_worker.error.connect(self.on_story_info_error)
        self.info_worker.start()

    def on_story_info_loaded(self, info: dict):
        """Handle story info loaded."""
        self.info_loading_label.setVisible(False)
        self.story_name_label.setText(info['story_name'])

        # Format total chapters
        total_ch = info['total_chapters']
        if total_ch == 'N/A' or 'Không hỗ trợ' in total_ch:
            self.total_chapters_label.setText(total_ch)
        else:
            self.total_chapters_label.setText(f"{total_ch} chương")

    def on_story_info_error(self, error: str):
        """Handle story info load error."""
        self.info_loading_label.setVisible(False)
        self.story_name_label.setText("Không lấy được thông tin")
        self.total_chapters_label.setText("N/A")
        print(f"Error fetching story info: {error}")
    
    def upload_link_file(self):
        """Upload a text file containing links."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file chứa link",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.multi_link_input.setText(content)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể đọc file:\n{str(e)}")
    
    def start_scraping(self):
        """Start the scraping process."""
        url = self.url_input.toPlainText().strip()

        if not url and not self.multi_link_input.toPlainText().strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập link truyện")
            return
        
        if not self.detected_config:
            self.detect_website()
            if not self.detected_config:
                return
        
        # Reset
        self.scraped_chapters = []
        self.processed_chapters = []
        self.results_list.clear()
        self.save_btn.setEnabled(False)
        
        # Show progress
        self.progress_frame.setVisible(True)
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        
        if self.detected_config['type'] == 'spa':
            # Use Selenium for SPA websites
            from_chapter = self.from_chapter_spin.value()
            to_chapter = self.to_chapter_spin.value()

            if from_chapter > to_chapter:
                QMessageBox.warning(self, "Lỗi", "Chương bắt đầu phải nhỏ hơn chương kết thúc")
                self.progress_frame.setVisible(False)
                self.start_btn.setEnabled(True)
                return

            # Use first URL for SPA
            first_url = url.split('\n')[0].strip()
            self.scraper_worker = SPAScraperWorker(first_url, from_chapter, to_chapter, self.detected_config)
        else:
            # Use BeautifulSoup for static websites
            # Priority: main url_input -> multi_link_input
            if url:
                links = [(i+1, link.strip()) for i, link in enumerate(url.split('\n')) if link.strip()]
            else:
                links_text = self.multi_link_input.toPlainText().strip()
                if links_text:
                    links = [(i+1, link.strip()) for i, link in enumerate(links_text.split('\n')) if link.strip()]
                else:
                    links = []

            if not links:
                QMessageBox.warning(self, "Lỗi", "Không có link nào để xử lý")
                self.progress_frame.setVisible(False)
                self.start_btn.setEnabled(True)
                return

            self.scraper_worker = StaticScraperWorker(links, self.detected_config)
        
        self.scraper_worker.progress.connect(self.on_scrape_progress)
        self.scraper_worker.chapter_done.connect(self.on_chapter_done)
        self.scraper_worker.finished.connect(self.on_scrape_finished)
        self.scraper_worker.error.connect(self.on_error)
        self.scraper_worker.start()
    
    def cancel_scraping(self):
        """Cancel the scraping process."""
        if self.scraper_worker and self.scraper_worker.isRunning():
            self.scraper_worker.cancel()
        if self.claude_worker and self.claude_worker.isRunning():
            self.claude_worker.cancel()
        if self.batch_worker and self.batch_worker.isRunning():
            self.batch_worker.cancel()
    
    def on_scrape_progress(self, message: str, current: int, total: int):
        """Handle scraping progress update."""
        self.progress_label.setText(message)
        self.progress_count.setText(f"{current}/{total}")
        if total > 0:
            self.progress_bar.setValue(int(current / total * 100))
    
    def on_chapter_done(self, chapter_num: int, title: str, content: str):
        """Handle chapter scraping done."""
        self.scraped_chapters.append((chapter_num, title, content))
        self.results_list.append(f"✅ {title} ({len(content)} ký tự)")
    
    def on_scrape_finished(self, results: list):
        """Handle scraping finished."""
        self.scraped_chapters = results
        
        if not results:
            self.progress_frame.setVisible(False)
            self.start_btn.setEnabled(True)
            QMessageBox.warning(self, "Lỗi", "Không lấy được nội dung nào")
            return
        
        # Check if Claude processing is needed
        if self.level_claude.isChecked():
            self.start_claude_processing()
        elif self.level_batch.isChecked():
            self.start_batch_processing()
        else:
            self.processed_chapters = results
            self.on_all_finished()
    
    def start_claude_processing(self):
        """Start Claude processing."""
        if not self.project_id:
            self.processed_chapters = self.scraped_chapters
            self.on_all_finished()
            return

        # Get project data
        project = db.get_project(self.project_id)
        instructions = project['instructions'] if project else ""

        # Get memory items and format them
        memory_items = db.get_memory(self.project_id) or []
        memory = "\n".join([
            f"**{item['category']}** - {item['key']}: {item['value']}"
            for item in memory_items
        ]) if memory_items else ""

        # Get glossary formatted for prompt
        glossary = db.get_glossary_for_prompt(self.project_id)

        # Get project-specific model and thinking settings
        project = db.get_project(self.project_id)
        project_model = project.get('model') if project else None
        extended_thinking = bool(project.get('extended_thinking', 1)) if project else True

        self.results_list.append("\n--- Bắt đầu xử lý với Claude ---\n")

        self.claude_worker = ClaudeProcessWorker(self.scraped_chapters, instructions, memory, glossary,
                                                  project_model, extended_thinking)
        self.claude_worker.progress.connect(self.on_scrape_progress)
        self.claude_worker.chapter_done.connect(self.on_claude_chapter_done)
        self.claude_worker.finished.connect(self.on_claude_finished)
        self.claude_worker.error.connect(self.on_error)
        self.claude_worker.start()
    
    def on_claude_chapter_done(self, chapter_num: int, title: str, content: str):
        """Handle Claude processing done for a chapter."""
        self.results_list.append(f"✨ Claude: {title} ({len(content)} ký tự)")

        # Auto-detect and add memory from processed chapter
        if self.project_id:
            auto_detect_and_add_memory(content, self.project_id)
    
    def on_claude_finished(self, results: list):
        """Handle Claude processing finished."""
        self.processed_chapters = results
        self.on_all_finished()

    def start_batch_processing(self):
        """Start Batch API processing."""
        if not self.project_id:
            self.processed_chapters = self.scraped_chapters
            self.on_all_finished()
            return

        # Get project data
        project = db.get_project(self.project_id)
        instructions = project['instructions'] if project else ""

        # Get memory items and format them
        memory_items = db.get_memory(self.project_id) or []
        memory = "\n".join([
            f"**{item['category']}** - {item['key']}: {item['value']}"
            for item in memory_items
        ]) if memory_items else ""

        # Get glossary formatted for prompt
        glossary = db.get_glossary_for_prompt(self.project_id)

        # Get project-specific model and thinking settings
        project = db.get_project(self.project_id)
        project_model = project.get('model') if project else None
        extended_thinking = bool(project.get('extended_thinking', 1)) if project else True

        self.results_list.append("\n--- Bắt đầu xử lý với Batch API ---\n")
        self.results_list.append("⏳ Batch processing có thể mất vài phút...\n")

        self.batch_worker = BatchProcessWorker(self.scraped_chapters, instructions, memory, glossary,
                                               project_model, extended_thinking)
        self.batch_worker.progress.connect(self.on_scrape_progress)
        self.batch_worker.finished.connect(self.on_batch_finished)
        self.batch_worker.error.connect(self.on_error)
        self.batch_worker.start()

    def on_batch_finished(self, results: list):
        """Handle Batch processing finished."""
        self.processed_chapters = results
        self.results_list.append("\n✅ Batch processing hoàn thành!")

        # Auto-detect and add memory from all processed chapters
        if self.project_id:
            for chapter_num, title, content in results:
                self.results_list.append(f"✨ {title} ({len(content)} ký tự)")
                auto_detect_and_add_memory(content, self.project_id)
        else:
            for chapter_num, title, content in results:
                self.results_list.append(f"✨ {title} ({len(content)} ký tự)")

        self.on_all_finished()

    def on_all_finished(self):
        """Handle all processing finished."""
        self.progress_frame.setVisible(False)
        self.start_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        total_chars = sum(len(c[2]) for c in self.processed_chapters)
        self.results_list.append(f"\n✅ Hoàn thành! {len(self.processed_chapters)} chương, {total_chars:,} ký tự")
        
        QMessageBox.information(
            self,
            "Hoàn thành",
            f"Đã lấy xong {len(self.processed_chapters)} chương!\n"
            f"Tổng: {total_chars:,} ký tự\n\n"
            "Nhấn 'Lưu kết quả' để lưu file."
        )
    
    def on_error(self, error: str):
        """Handle error."""
        self.progress_frame.setVisible(False)
        self.start_btn.setEnabled(True)
        QMessageBox.critical(self, "Lỗi", error)
    
    def save_results(self):
        """Save results to files."""
        if not self.processed_chapters:
            QMessageBox.warning(self, "Lỗi", "Không có nội dung để lưu")
            return
        
        # Ask for save location
        if self.output_separate.isChecked():
            # Save as separate files
            folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu")
            if not folder:
                return
            
            saved_count = 0
            for chapter_num, title, content in self.processed_chapters:
                # Extract real chapter number from title
                real_chapter_num = extract_chapter_number(title)
                if real_chapter_num == 0:
                    real_chapter_num = chapter_num  # Fallback to sequential number

                # Filename is just the chapter number
                filename = f"{real_chapter_num}.txt"
                filepath = os.path.join(folder, filename)
                
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"{title}\n\n{content}")
                    saved_count += 1
                except Exception as e:
                    print(f"Error saving {filename}: {e}")
            
            # Add to project files if checked
            if self.add_to_files_check.isChecked() and self.project_id:
                for chapter_num, title, content in self.processed_chapters:
                    # Extract real chapter number
                    real_chapter_num = extract_chapter_number(title)
                    if real_chapter_num == 0:
                        real_chapter_num = chapter_num

                    filename = f"{real_chapter_num}.txt"
                    filepath = os.path.join(folder, filename)
                    if os.path.exists(filepath):
                        db.add_file(self.project_id, filepath, filename)
            
            QMessageBox.information(
                self,
                "Thành công",
                f"Đã lưu {saved_count} file vào:\n{folder}"
            )
        else:
            # Save as single merged file
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Lưu file",
                "truyen_merged.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if not file_path:
                return
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for chapter_num, title, content in self.processed_chapters:
                        f.write(f"{'='*60}\n")
                        f.write(f"{title}\n")
                        f.write(f"{'='*60}\n\n")
                        f.write(content)
                        f.write("\n\n")
                
                # Add to project files if checked
                if self.add_to_files_check.isChecked() and self.project_id:
                    filename = os.path.basename(file_path)
                    db.add_file(self.project_id, file_path, filename)
                
                QMessageBox.information(
                    self,
                    "Thành công",
                    f"Đã lưu file:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể lưu file:\n{str(e)}")
