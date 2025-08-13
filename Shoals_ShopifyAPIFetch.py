import os
import requests
from datetime import datetime
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

key_vault_name = "ShoalsAzureKeyVault"
secret_name = "ShoalsAPISecret"

# Construct the vault URL
KVUri = f"https://{key_vault_name}.vault.azure.net"

# Use managed identity (DefaultAzureCredential handles it automatically inside the VM)
credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)

# Retrieve the secret
retrieved_secret = client.get_secret(secret_name)

# 🔐 API Creds
SHOP_NAME = "shoals-engraving"  
ACCESS_TOKEN = retrieved_secret.value
API_VERSION = "2024-04"

# 🔗 REST API base URL
base_url = f"https://{SHOP_NAME}.myshopify.com/admin/api/{API_VERSION}/orders.json"
headers = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# First request parameters (no date filter for all-time)
params = {
    "limit": 250,
    "status": "any",
    "fields": "id,created_at,name,total_price,line_items"
}

all_orders = []
page_count = 0

while True:
    page_count += 1
    print(f"Fetching page {page_count}...")

    response = requests.get(base_url, headers=headers, params=params)
    data = response.json()
    orders = data.get("orders", [])
    if not orders:
        break

    all_orders.extend(orders)

    # Check for pagination
    if "Link" in response.headers:
        links = response.headers["Link"].split(",")
        next_url = None
        for link in links:
            if 'rel="next"' in link:
                next_url = link.split(";")[0].strip("<> ")
        if next_url:
            base_url = next_url
            params = {}  # URL already has params
        else:
            break
    else:
        break

print(f"Total orders fetched: {len(all_orders)}")

# Create DataFrames
df_orders = pd.json_normalize(all_orders)
df_items = pd.json_normalize(
    all_orders,
    record_path=["line_items"],
    meta=["id", "name", "created_at", "total_price"],
    record_prefix="item_",
    sep="_"
)

# 📁 Save CSV in same directory as script
script_dir = r"C:\Users\myAzVm\Desktop\Shopify"
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = os.path.join(script_dir, f"ShopifyOrders_{timestamp}.csv")

df_items.to_csv(filename, index=False)
print(f"CSV saved to: {filename}")
