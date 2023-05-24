"""This script checks for updates on the IRCC portal and sends a notification if there is an update.

@Author: Jibran Haider

Example
-------
To run the script, use the following command:

    $ python check_ircc_updates.py

Notes
-----
This script uses Selenium to automate a web browser. Selenium is a tool for automating web browsers.
The script uses the Safari WebDriver, but you can use any WebDriver you want. You can download the WebDriver for your browser here: https://www.selenium.dev/downloads/

"""
import datetime

from typing import KeysView
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import time
import datetime

# Constants
USERNAME = ""
PASSWORD = ""
LOGIN_URL = "https://tracker-suivi.apps.cic.gc.ca/en/login"
DASHBOARD_URL = "https://tracker-suivi.apps.cic.gc.ca/en/dashboard"
CHECK_INTERVAL_SECONDS = 6 * 60 * 60  # 6 hours
LAST_UPDATED_FILE = "last_updated.txt"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_ADDRESS = "syedjbhaider@gmail.com"
EMAIL_PASSWORD = ""
PUSHOVER_USER = ""
PUSHOVER_TOKEN = ""

def send_email(subject, body):
    """Send an email using the Gmail SMTP server.

    Parameters
    ----------
    subject : str
        The subject of the email.
    body : str
        The body of the email.

    Returns
    -------
    None

    Notes
    -----
    This function uses the Gmail SMTP server to send an email. The Gmail SMTP server requires authentication.
    """
    try:
        # MIMEMultipart() is used to create a message object that is attached with MIME headers and a body. MIME stands for Multipurpose Internet Mail Extensions.
        msg = MIMEMultipart()       
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))     # Attach the body of the email to the MIME message object.

        # Create a secure SSL context
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)       # This line of code creates a secure SSL context and creates an SMTP object.
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"An error occurred while sending email: {e}")


def send_push_notification(title, message):
    try:
        url = "https://api.pushover.net/1/messages.json"
        data = {
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "title": title,
            "message": message
        }
        requests.post(url, data=data)
    except Exception as e:
        print(f"An error occurred while sending push notification: {e}")


def check_for_updates():
    """Check for updates on the IRCC portal and send a notification if there is an update.
    
    This function uses Selenium to log in to the IRCC portal and check the "Last updated" date on the dashboard page.
    If the "Last updated" date has changed since the last time the script ran, a notification is sent.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Notes
    -----
    This function uses Selenium to automate a web browser. Selenium is a tool for automating web browsers.
    """
    try:
        #
        # Initialize the WebDriver and open the login page
        #
        driver = webdriver.Safari()     # initialize the WebDriver
        driver.get(LOGIN_URL)     # open the login page
        driver.maximize_window()        # maximize the window
        # Add a wait to ensure the page has fully loaded
        wait = WebDriverWait(driver, 10)


        #
        # Log in
        #
        # Wait for the username field to be located
        try:
            username_field = wait.until(
                EC.element_to_be_clickable((By.ID, "uci"))
            )
        except TimeoutException:
            print("TimeoutException: The username field wasn't located after 10 seconds.")
            send_email("IRCC Portal Script Error", "TimeoutException: The username field wasn't located after 10 seconds.")
            # send_push_notification("IRCC Portal Script Error", "TimeoutException: The username field wasn't located after 10 seconds.")
            return
        # username_field = driver.find_element(By.ID, value="uci")
        username_field.send_keys(USERNAME)
        # Wait for the password field to be located
        # WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "password")))
        try:
            password_field = wait.until(
                EC.element_to_be_clickable((By.ID, "password"))
            )
            # Check if the password field is selected
            if driver.switch_to.active_element != password_field:
                # If not, click the password field to select it
                password_field.click()
        except TimeoutException:
            print("TimeoutException: The password field wasn't located after 10 seconds.")
            send_email("IRCC Portal Script Error", "TimeoutException: The password field wasn't located after 10 seconds.")
            # send_push_notification("IRCC Portal Script Error", "TimeoutException: The password field wasn't located after 10 seconds.")
            return
        # password_field = driver.find_element(By.ID, value="password")
        password_field.send_keys(PASSWORD)
        # input("Press Enter to continue...")
        # Wait until the "Sign In" button is clickable
        try:
            sign_in_button = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'btn-sign-in'))
            )
        except TimeoutException:
            print("TimeoutException: The \'Sign In\' buttom wasn't clickable after 10 seconds.")
            send_email("IRCC Portal Script Error", "TimeoutException: The \'Sign In\' buttom wasn't clickable after 10 seconds.")
            return
        # Click the "Sign In" button
        # sign_in_button.click()
        # driver.execute_script("arguments[0].click();", sign_in_button)
        password_field.send_keys(Keys.RETURN)

        # # Go to the dashboard page
        # driver.get(DASHBOARD_URL)

        #
        # Check for new updates
        #
        # Wait for the "Updated" field to be located
        try:
            updated_date = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "date-text"))
            ).text
        except TimeoutException:
            print("TimeoutException: The \'Updated\' field wasn't located after 10 seconds.")
            send_email("IRCC Portal Script Error", "TimeoutException: The \'Updated\' field wasn't located after 10 seconds.")
            return
        # Get the "Last updated" date
        # updated_date = driver.find_element(By.CLASS_NAME, "date-text").text

        # Check if the "Last updated" date has changed since the last time the script ran
        try:
            with open(LAST_UPDATED_FILE, "r") as f:
                last_updated_date = f.read().strip()
        except FileNotFoundError:
            last_updated_date = None

        if updated_date != last_updated_date:
            # If the "Last updated" date has changed, send a notification and update the last updated date
            send_email("IRCC Portal Update", f"The IRCC portal was updated on {updated_date}.")
            # send_push_notification("IRCC Portal Update", f"The IRCC portal was updated on {updated_date}.")

            with open(LAST_UPDATED_FILE, "w") as f:
                f.write(updated_date)


        # get current date and time
        now = datetime.datetime.now()
        # format as a string
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        # use timestamp in filename
        driver.save_screenshot(f"screenshots/{timestamp}-ss_ircc_portal.png")

        # Close the WebDriver
        driver.quit()

    except Exception as e:
        print(f"An error occurred while checking for updates: {e}")
        send_email("IRCC Portal Script Error", f"An error occurred while checking for updates: {e}")
        # send_push_notification("IRCC Portal Script Error", f"An error occurred while checking for updates: {e}")


def main():
    """Run the script continuously.

    This main function runs the script continuously. The script checks for updates every CHECK_INTERVAL_SECONDS seconds.
    """
    while True:
        check_for_updates()
        time.sleep(CHECK_INTERVAL_SECONDS)      # sleep for CHECK_INTERVAL_SECONDS seconds

if __name__ == "__main__":
    main()
