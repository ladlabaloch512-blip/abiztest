import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.logger import get_logger

logger = get_logger("FB_Automation")

class FacebookAutomation:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)

    def login(self, username, password):
        try:
            self.driver.get("https://www.facebook.com/")

            # Check if already logged in by looking for the profile element or home icon
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='banner']")))
                logger.info(f"Already logged in as {username}")
                return True
            except:
                pass # Not logged in, proceed

            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            pass_input = self.driver.find_element(By.ID, "pass")

            email_input.clear()
            email_input.send_keys(username)
            time.sleep(1)

            pass_input.clear()
            pass_input.send_keys(password)
            time.sleep(1)

            login_btn = self.driver.find_element(By.NAME, "login")
            login_btn.click()

            # Wait for successful login (e.g., banner loads)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='banner']")))
            logger.info(f"Successfully logged in as {username}")
            return True
        except Exception as e:
            logger.error(f"Login failed for {username}: {e}")
            return False

    def solve_need_attention(self):
        # Stub for the requested "Need Attention" / Number verification solver
        # If the specific screen appears, wait for user input
        try:
            attention_elem = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Need Attention') or contains(text(), 'Verify your number')]")
            if attention_elem:
                logger.warning("Need Attention screen detected. Waiting for manual user input.")
                # We could pause automation here and notify UI
                return True
        except Exception as e:
            pass
        return False

    def auto_list_item(self, listing_data):
        """
        listing_data is a dict containing: title, price, category, description, images (list of paths), location
        """
        try:
            self.driver.get("https://www.facebook.com/marketplace/create/item")

            # Upload images
            if "images" in listing_data and listing_data["images"]:
                file_input = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
                # Selenium handles multiple files by passing paths separated by newline
                file_input.send_keys("\n".join(listing_data["images"]))
                time.sleep(3)

            # Fill Title
            title_input = self.wait.until(EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Title']//input")))
            title_input.send_keys(listing_data.get("title", ""))

            # Fill Price
            price_input = self.driver.find_element(By.XPATH, "//label[@aria-label='Price']//input")
            price_input.send_keys(str(listing_data.get("price", "")))

            # Further elements like Category, Condition, Description would be filled here.
            # Due to FB's dynamic obfuscated classes, it's best to fetch exact selectors from the ConfigManager
            # e.g., selectors = ConfigManager().get("selectors")

            logger.info(f"Filled listing data for: {listing_data.get('title')}")

            # Click Publish (stub)
            # publish_btn = self.driver.find_element(By.XPATH, "//div[@aria-label='Publish']")
            # publish_btn.click()

            return True
        except Exception as e:
            logger.error(f"Auto listing failed: {e}")
            return False
