import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.logger import get_logger

logger = get_logger("FB_Messenger")

class MessengerManager:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    def check_new_messages(self):
        try:
            self.driver.get("https://www.facebook.com/messages/t/")
            # Wait for message list to load
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Chats']")))

            # Find unread messages (this selector will need to be dynamic via config)
            unread_elements = self.driver.find_elements(By.XPATH, "//div[contains(@aria-label, 'Unread')]")

            messages = []
            for elem in unread_elements:
                sender = elem.get_attribute("aria-label").split("Unread, ")[-1]
                messages.append({"sender": sender, "element": elem})

            return messages
        except Exception as e:
            logger.error(f"Failed to check messages: {e}")
            return []

    def send_reply(self, thread_element, message_text):
        try:
            # Click thread
            thread_element.click()
            time.sleep(2)

            # Find input box and send
            input_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Message']")))
            input_box.send_keys(message_text)

            # Find send button and click (or hit Enter)
            send_btn = self.driver.find_element(By.XPATH, "//div[@aria-label='Press Enter to send']")
            send_btn.click()

            logger.info("Reply sent successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            return False
