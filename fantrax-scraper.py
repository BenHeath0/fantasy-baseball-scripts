import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pickle
import os

# Set up Selenium WebDriver (make sure chromedriver is in your PATH)
service = Service("/opt/homebrew/bin/chromedriver")  # Update with the correct path
driver = webdriver.Chrome(service=service)

# URL to scrape
url = "https://www.fantrax.com/fantasy/league/3pzlfabym4af1a3o/players;statusOrTeamFilter=ALL;pageNumber=1;searchName=;miscDisplayType=1;positionOrGroup=ALL;maxResultsPerPage=500"

# Authenticate only once and reuse cookies
cookies_file = "fantrax_cookies.pkl"


def authenticate():
    driver.get("https://www.fantrax.com/login")
    input("Please log in manually, then press Enter...")
    pickle.dump(driver.get_cookies(), open(cookies_file, "wb"))


if not os.path.exists(cookies_file):
    authenticate()

# Load cookies for authenticated session
driver.get("https://www.fantrax.com")
cookies = pickle.load(open(cookies_file, "rb"))
for cookie in cookies:
    driver.add_cookie(cookie)

# Open the page
driver.get(url)

# Wait until the table loads (adjust timeout and element locator if necessary)
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.ID, "league-players-stats"))
)

# Give extra time to ensure JavaScript loaded the full content
time.sleep(2)

# Parse the page source with BeautifulSoup
soup = BeautifulSoup(driver.page_source, "html.parser")

# Find the table (adjust selectors if necessary)
table = soup.find("ultimate-table", id="league-players-stats").find("table")

# Extract table headers
header_parent = (
    soup.find("ultimate-table", id="league-players-stats").find("header").find("tbody")
)
headers = [th.get_text(strip=True) for th in header_parent.find_all("th")]

# Extract table rows
# TODO: This is where this stops working. table is too gross.
data = []
for row in table.find_all("tr"):
    cols = [td.get_text(strip=True) for td in row.find_all("td")]
    data.append(cols)

# Create DataFrame
df = pd.DataFrame(data, columns=headers)

# Save to CSV
df.to_csv("fantrax_players.csv", index=False)

# Close the browser
driver.quit()

print("Data has been successfully scraped and saved to fantrax_players.csv")
