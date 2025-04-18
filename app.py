from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time

search_text = input("🔍 Enter the text to search for: ").strip()
start = int(input("Enter start sitemap number: "))
end = int(input("Enter end sitemap number: "))
base_url = "https://cinego.tv/sitemap-movie-{}.xml"

edge_driver_path = r"D:\edge driver\edgedriver_win64\msedgedriver.exe"  # ⬅️ Change this to your extracted file path

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")

service = Service(executable_path=edge_driver_path)
driver = webdriver.Edge(service=service, options=options)

for number in range(start, end + 1):
    url = base_url.format(number)
    print(f"\n🔗 Checking: {url}")
    try:
        driver.get(url)
        time.sleep(1)
        if search_text.lower() in driver.page_source.lower():
            print(f"✅ Match found on: {url}")
        else:
            print("❌ No match found.")
    except Exception as e:
        print(f"⚠️ Error accessing {url}: {e}")
    time.sleep(1.5)

driver.quit()
print("\n✅ Search complete!")
