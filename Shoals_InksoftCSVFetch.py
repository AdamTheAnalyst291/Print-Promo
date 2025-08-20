import os
import shutil
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# === Load credentials securely ===
key_vault_name = "ShoalsAzureKeyVault"
secret_name = "ShoalsInksoftSecret"

# Construct the vault URL
KVUri = f"https://{key_vault_name}.vault.azure.net"

# Use managed identity (DefaultAzureCredential handles it automatically inside the VM)
credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)

# Retrieve the secret
retrieved_secret = client.get_secret(secret_name)

USERNAME = "sales@shoalsprintpromo.com"
PASSWORD = retrieved_secret.value

download_dir = "C:\\Users\\myAzVm\\Downloads"
target_dir = "C:\\Users\\myAzVm\\Desktop\\InkSoft"
filename_prefix = "Order Detail Report"
timeout = 30  # seconds

def clean_download_folder():
    for f in os.listdir(download_dir):
        if f.startswith(filename_prefix) and (f.endswith(".csv") or f.endswith(".crdownload")):
            try:
                os.remove(os.path.join(download_dir, f))
                print(f"🗑️ Deleted: {f}")
            except Exception as e:
                print(f"⚠️ Could not delete {f}: {e}")

clean_download_folder()

# === Launch browser ===
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

# === Step 1: Navigate to login page ===
driver.get("https://stores.inksoft.com/Shoals_Print_And_Promo/shop/account/login?ReturnUrl=%2FShoals_Print_And_Promo%2Fadmin%2Fordermanager%2Forders%3FStatus%3DOpen%26Index%3D0%26MaxResults%3D25%26OrderByDirection%3DDescending%26OrderBy%3DDateCreated")

# === Step 2: Fill in credentials ===
email_input = wait.until(EC.presence_of_element_located((By.ID, "emailAddress")))
password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))

email_input.send_keys(USERNAME)
password_input.send_keys(PASSWORD)

# === Step 3: Wait for login button to become enabled ===
wait.until(lambda d: d.find_element(By.ID, "loginButton").is_enabled())

# === Step 4: Click login ===
driver.find_element(By.ID, "loginButton").click()

# === Step 5: Wait for redirect to orders page ===
time.sleep(10)

try:
    driver.get("https://stores.inksoft.com/Shoals_Print_And_Promo/admin/reporting?reportType=orderDetail")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "report-container")))  # Adjust selector
except Exception as e:
    print("Navigation to report page failed:", e)


# Wait for and click the dropdown
# Click the dropdown first
wait.until(EC.element_to_be_clickable((By.ID, "dateRangeMenu"))).click()

# Wait for the menu panel to appear
wait.until(EC.visibility_of_element_located((By.ID, "mat-menu-panel-1")))

# Select the "This year" option
this_year_button = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//button[.//span[contains(text(), 'This year')]]")
))
this_year_button.click()
print("✅ 'This year' selected.")

# Assuming driver is already initialized and page is loaded
try:
    export_button = wait.until(
        EC.element_to_be_clickable((By.ID, "exportCSVBtn"))
    )
    export_button.click()
    print("✅ Export CSV button clicked.")
except Exception as e:
    print(f"⚠️ Failed to click Export CSV button: {e}")

current_year = datetime.now().year
new_filename = f"InkSoft_OrdersReport_{current_year}.csv"
target_path = os.path.join(target_dir, new_filename)

def wait_for_latest_download():
    for _ in range(timeout):
        files = [
            f for f in os.listdir(download_dir)
            if f.startswith(filename_prefix) and f.endswith(".csv")
        ]
        if files:
            files.sort(key=lambda f: os.path.getmtime(os.path.join(download_dir, f)), reverse=True)
            latest_file = files[0]
            full_path = os.path.join(download_dir, latest_file)
            if not latest_file.endswith(".crdownload"):
                return full_path
        time.sleep(1)
    return None

downloaded_file = wait_for_latest_download()

# === Move and rename ===
if downloaded_file:
    try:
        shutil.move(downloaded_file, target_path)
        print(f"✅ File moved and renamed to: {target_path}")
    except Exception as e:
        print(f"⚠️ Failed to move file: {e}")
else:
    print("⚠️ No completed download found.")
