import os
import requests
import time
import csv
import chromedriver_autoinstaller
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Auto-install ChromeDriver
chromedriver_autoinstaller.install()

# Headless browser config (important for GitHub runners)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)

# Slack configuration
slack_webhook_url = "https://hooks.slack.com/services/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"

# Track start time of status changes
status_start_times = {}

# CSV setup: Add headers if file doesn't exist
log_file = "camera_logs.csv"
if not os.path.exists(log_file):
    with open(log_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Camera ID", "Status", "Start Time", "End Time", "Duration (mins)"])

# Function to send Slack notifications
def send_slack_notification(camera_id, status):
    message = f"Camera {camera_id} status changed: {status}"
    payload = {"text": message}
    try:
        response = requests.post(slack_webhook_url, json=payload)
        if response.status_code != 200:
            print(f"Slack notification failed: {response.text}")
        else:
            print(f"Notification sent to Slack for {camera_id}: {status}")
    except Exception as e:
        print(f"Error sending Slack notification: {e}")

# Function to check the camera status and log data
def check_camera_status():
    driver.get("https://support.landmarksea.oly.live/dashboard")

    # Wait for the table to load
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table tbody tr')))
    except Exception as e:
        print(f"Error loading page: {e}")
        return

    # Find the table rows
    rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
    for row in rows:
        camera_id = row.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        status_color = row.get_attribute("class")
        status = ""

        if 'highlight-critical' in status_color:
            status = 'AI not working (Red)'
        elif 'highlight-inactive' in status_color:
            status = 'Camera inactive (Yellow)'

        if status:
            timestamp = datetime.now()
            start_time = status_start_times.get(camera_id, timestamp)
            duration = (timestamp - start_time).total_seconds() / 60

            # Save log entry to CSV
            with open(log_file, mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, camera_id, status, start_time, timestamp, duration])

            # Update the start time for next round
            status_start_times[camera_id] = timestamp

            # Send Slack notification
            send_slack_notification(camera_id, status)

    print(f"Status checked and logged at {datetime.now()}")

# Run once and quit
try:
    check_camera_status()
finally:
    driver.quit()
