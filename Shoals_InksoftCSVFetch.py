import os
import shutil
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# === Configuration ===
KEY_VAULT_NAME = "ShoalsAzureKeyVault"
SECRET_NAME = "ShoalsInksoftSecret"
USERNAME = "sales@shoalsprintpromo.com"
DOWNLOAD_DIR = "C:\\Users\\myAzVm\\Downloads"
TARGET_DIR = "C:\\Users\\myAzVm\\Desktop\\InkSoft"
FILENAME_PREFIX = "Order Detail Report"
TIMEOUT = 30  # seconds
LOGIN_URL = "https://stores.inksoft.com/Shoals_Print_And_Promo/shop/account/login?ReturnUrl=%2FShoals_Print_And_Promo%2Fadmin%2Fordermanager%2Forders%3FStatus%3DOpen%26Index%3D0%26MaxResults%3D25%26OrderByDirection%3DDescending%26OrderBy%3DDateCreated"
REPORT_URL = "https://stores.inksoft.com/Shoals_Print_And_Promo/admin/reporting?reportType=orderDetail"
LANDING_URL = "https://stores.inksoft.com/Shoals_Print_And_Promo/admin/ordermanager/orders"

# === Logging Setup ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Secure Credential Retrieval ===
def get_password_from_keyvault():
    kv_uri = f"https://{KEY_VAULT_NAME}.vault.azure.net"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=kv_uri, credential=credential)
    secret = client.get_secret(SECRET_NAME)
    return secret.value

# === File Cleanup ===
def clean_download_folder():
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith(FILENAME_PREFIX) and (f.endswith(".csv") or f.endswith(".crdownload")):
            try:
                os.remove(os.path.join(DOWNLOAD_DIR, f))
                logging.info(f"Deleted old file: {f}")
            except Exception as e:
                logging.warning(f"Could not delete {f}: {e}")

# === Login Automation ===
def login(driver, wait, username, password):
    driver.get(LOGIN_URL)
    wait.until(EC.presence_of_element_located((By.ID, "emailAddress"))).send_keys(username)
    wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
    wait.until(lambda d: d.find_element(By.ID, "loginButton").is_enabled())
    driver.find_element(By.ID, "loginButton").click()

# === Report Navigation ===
def navigate_to_report(driver, wait, landing_url, report_url):
    wait.until(lambda d: d.current_url.startswith(landing_url))
    logging.info("✅ Login redirect confirmed.")
    driver.get(report_url)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "reports-container")))
    logging.info("✅ Report page loaded.")

# === Date Range Selection ===
def select_this_year(wait):
    wait.until(EC.element_to_be_clickable((By.ID, "dateRangeMenu"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "mat-menu-panel-1")))
    this_year_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[.//span[contains(text(), 'This year')]]")
    ))
    this_year_button.click()
    logging.info("Selected 'This year' date range.")

# === CSV Export ===
def export_csv(wait):
    try:
        export_button = wait.until(EC.element_to_be_clickable((By.ID, "exportCSVBtn")))
        export_button.click()
        logging.info("Clicked Export CSV button.")
    except Exception as e:
        logging.error(f"Failed to click Export CSV button: {e}")

# === Download Wait Logic ===
def wait_for_latest_download():
    for _ in range(TIMEOUT):
        files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith(FILENAME_PREFIX) and f.endswith(".csv")]
        if files:
            files.sort(key=lambda f: os.path.getmtime(os.path.join(DOWNLOAD_DIR, f)), reverse=True)
            latest_file = files[0]
            full_path = os.path.join(DOWNLOAD_DIR, latest_file)
            if not latest_file.endswith(".crdownload"):
                return full_path
        time.sleep(1)
    return None

# === Move and Rename File ===
def move_downloaded_file(downloaded_file, target_path):
    try:
        shutil.move(downloaded_file, target_path)
        logging.info(f"File moved and renamed to: {target_path}")
    except Exception as e:
        logging.error(f"Failed to move file: {e}")

# === Main Flow ===
def main():
    password = get_password_from_keyvault()
    clean_download_folder()

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    try:
        login(driver, wait, USERNAME, password)
        navigate_to_report(driver, wait, LANDING_URL, REPORT_URL)
        select_this_year(wait)
        export_csv(wait)

        current_year = datetime.now().year
        new_filename = f"InkSoft_OrdersReport_{current_year}.csv"
        target_path = os.path.join(TARGET_DIR, new_filename)

        downloaded_file = wait_for_latest_download()
        if downloaded_file:
            move_downloaded_file(downloaded_file, target_path)
        else:
            logging.warning("No completed download found.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()