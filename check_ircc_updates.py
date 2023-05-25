"""This script checks for updates on the IRCC portal and sends a notification if there is an update.

@Author: Jibran Haider

Example
-------
To run the script, use the following command:

    $ python check_ircc_updates.py

To run the script in the background, use the following command:

    $ nohup python check_ircc_updates.py > output.log &

Or if you have opened a screen session and want to run the script with output displayed in both the terminal and the log file, use the following command (where -u is used to force the output to be unbuffered):

    $ `python -u check_ircc_updates.py | tee output.log`

If you then want to kill the process, use the following command:

    $ ps aux | grep 'check_ircc_updates.py' | grep -v grep
    $ kill -9 <PID>

Notes
-----
This script uses Selenium to automate a web browser. Selenium is a tool for automating web browsers.
The script uses the Safari WebDriver, but you can use any WebDriver you want. You can download the WebDriver for your browser here: https://www.selenium.dev/downloads/

"""
import datetime
import json
import os
import smtplib
import sys
import time
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import traceback

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

with open('config.json') as f:
    config = json.load(f)

# Constants
USERNAME = config['USERNAME']
PASSWORD = config['PASSWORD']
SMTP_SERVER = config['SMTP_SERVER']
SMTP_PORT = config['SMTP_PORT']
EMAIL_ADDRESS = config['EMAIL_ADDRESS']
EMAIL_PASSWORD = config['EMAIL_PASSWORD']
PUSHOVER_USER = config['PUSHOVER_USER']
PUSHOVER_TOKEN = config['PUSHOVER_TOKEN']

LOGIN_URL = "https://tracker-suivi.apps.cic.gc.ca/en/login"
DASHBOARD_URL = "https://tracker-suivi.apps.cic.gc.ca/en/dashboard"
CHECK_INTERVAL_SECONDS = 1 * 60 * 60        # 1 hour
# CHECK_INTERVAL_SECONDS = 60        # 60 seconds
REINITIALIZATION_INTERVAL = 6 * 60 * 60        # 6 hours
LAST_UPDATED_FILE = "last_updated.txt"
SCREENSHOTS_DIR = "screenshots"

def setup_webdriver():
    """Set up the WebDriver and return it.

    Parameters
    ----------
    None

    Returns
    -------
    driver : selenium.webdriver (WebDriver)
        The WebDriver object.
    wait : selenium.webdriver.support.wait.WebDriverWait
        The WebDriverWait object.
    """
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")       # Disable the automation control warning
    options.add_argument("--headless")  # Run in headless mode

    driver = webdriver.Chrome(options=options)  # initialize the WebDriver
    driver.maximize_window()  # maximize the window
    wait = WebDriverWait(driver, 10)
    return driver, wait

def login(driver, wait):
    """Log in to the IRCC portal.

    Parameters
    ----------
    driver : selenium.webdriver (WebDriver)
        The WebDriver object.
    wait : selenium.webdriver.support.wait.WebDriverWait
        The WebDriverWait object.

    Returns
    -------
    None
    """
    print('\n---------------------------------------')
    print('----- NAVIGATING TO LOGIN PAGE...-----')
    print('---------------------------------------')
    driver.get(LOGIN_URL)  # open the login page
    driver.execute_script("document.body.style.zoom='30%'")

    print('---------------------------------------')
    print('----- SIGNING IN -----')
    print('---------------------------------------')

    # Wait for the username field to be located and input username
    username_field = wait.until(EC.element_to_be_clickable((By.ID, "uci")))
    username_field.send_keys(USERNAME)

    # Wait for the password field to be located and input password
    password_field = wait.until(EC.element_to_be_clickable((By.ID, "password")))
    # Check if the password field is selected
    # if driver.switch_to.active_element != password_field:
    #     # If not, click the password field to select it
    #     password_field.click()
    password_field.send_keys(PASSWORD)
    password_field.send_keys(Keys.RETURN)       # press enter
    # Wait until the "Sign In" button is clickable and click it
    # sign_in_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-sign-in')))
    # sign_in_button.click()
    
    # Add delay
    time.sleep(2)
    # Check if the login was successful
    if driver.current_url == DASHBOARD_URL:
        print('======')
        print('SIGN IN SUCCESSFUL...!')
        print('Current URL: ' + driver.current_url)
        print('======')
        return
    else:
        raise Exception("***Dashboard did not load inside login(). Current URL: " + driver.current_url + "***")

def check_for_updates(driver, wait):
    """Check for updates on the IRCC portal.

    Parameters
    ----------
    driver : selenium.webdriver (WebDriver)
        The WebDriver object.
    wait : selenium.webdriver.support.wait.WebDriverWait
        The WebDriverWait object.

    Returns
    -------
    None
    """
    print('\n---------------------------------------')
    print('----- CHECKING FOR UPDATE -----')
    print('---------------------------------------')
    driver.execute_script("document.body.style.zoom='30%'")
    # # Go to the dashboard page
    # driver.get(DASHBOARD_URL)

    # Wait for the "Updated" field to be located
    updated_date = wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "date-text"))
    ).text

    # Check if the "Last updated" date has changed since the last time the script ran
    with open(LAST_UPDATED_FILE, "r") as f:
        last_updated_date = f.read().strip()

    if updated_date != last_updated_date:
        print('======')
        print('UPDATE FOUND...!')
        print('======')

        update = True
        screenshot_path = take_screenshot(driver, update)
        send_notification(updated_date, update, screenshot_path)

        # Update the last updated date
        with open(LAST_UPDATED_FILE, "w") as f:
            f.write(updated_date)
    else:
        print('======')
        print('NO UPDATE FOUND...!')
        print('======')

        update = False
        screenshot_path = take_screenshot(driver)
        send_notification(updated_date, update, screenshot_path)

def take_screenshot(driver, update=False):
    """Take a screenshot of the IRCC portal.

    Parameters
    ----------
    driver : selenium.webdriver (WebDriver)
        The WebDriver object.
    update : bool (optional)
        Whether or not the IRCC portal was updated.

    Returns
    -------
    screenshot_path : str
        The path to the screenshot.
    """
    print('\n---------------------------------------')
    print('----- TAKING & SAVING SCREENSHOT -----')
    print('---------------------------------------')
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)

    if update:
        screenshot_filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-update.png"
    else:
        screenshot_filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-no_update.png"
    screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)

    driver.execute_script("document.body.style.zoom='30%'")
    driver.save_screenshot(screenshot_path)
    print('======')
    print('SCREENSHOT TAKEN & SAVED...!')
    print('======')

    return screenshot_path

def send_notification(updated_date, update, screenshot_path):
    """Send a notification that the IRCC portal has been updated.
    
    Parameters
    ----------
    updated_date : str
        The date the IRCC portal was updated.
    update : bool
        Whether or not the IRCC portal was updated.
    screenshot_path : str
        The path to the screenshot.

    Returns
    -------
    None
    """
    print('\n---------------------------------------')
    print('----- SENDING NOTIFICATION -----')
    print('---------------------------------------')

    # Get current date
    now = datetime.datetime.now()
    # Format date as "Month day, year"
    date_in_words = now.strftime("%B %d, %Y")
    # date_today = datetime.datetime.now.strftime("%B %d, %Y")

    if update:
        send_email("IRCC Portal Update", f"The IRCC portal was updated on {updated_date}.", screenshot_path)
    else:
        send_email("IRCC Portal Status", f"No update on the IRCC portal as of {date_in_words}.\n Last update was on {updated_date}.", screenshot_path)

    print('======')
    print('NOTIFICATION SENT SUCCESSFULLY...!')
    print('======')
    # send_push_notification("IRCC Portal Update", f"The IRCC portal was updated on {updated_date}.")

def send_email(subject, body, screenshot_path=None):
    """Send an email and attach a screenshot.

    Parameters
    ----------
    subject : str
        The subject of the email.
    body : str
        The body of the email.
    screenshot_path : str (optional)
        The path to the screenshot.

    Returns
    -------
    None
    """
    print('------ Sending email... ------')

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))
    print("Attached body to email.")

    try:
        if screenshot_path is not None:
            with open(screenshot_path, "rb") as f:
                # Attach the screenshot
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(screenshot_path))
                msg.attach(img)

            print("Attached screenshot to email.")

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)       # This line of code creates a secure SSL context and creates an SMTP object.
        # server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("Logged in to email server.")
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, text)
        print("Sent email.")
        server.quit()

        print('------ Email sent successfully...! ------')
    except Exception as e:
        print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print('!!!!!! EXCEPTION: OTHER inside send_email() !!!!!!!')
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(f"EMAIL SEND FAILED -- An error occurred: {e}")
        traceback.print_exc()
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
        return

def send_push_notification(title, message):
    """Send a push notification using Pushover.

    Parameters
    ----------
    title : str
        The title of the push notification.
    message : str
        The message of the push notification.

    Returns
    -------
    None
    """
    print('------ Sending push notification... ------')

    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "title": title,
        "message": message
    }
    response = requests.post(url, data=data)

    if response.status_code != 200:
        print(f"Failed to send push notification: {response.text}")

    print('------ Push notification sent successfully...! ------')

def main():
    """Main function.
    """
    print('\n\n=======================================')
    print('=======================================')
    print('=======================================')
    print('===== IRCC PORTAL UPDATE CHECKER ======')
    print('=======================================')
    print(f'|| Date & Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ||')
    print('=======================================')
    print('----- Initial WebDriver Setup... -----')
    print('=======================================')
    # Initial WebDriver setup
    driver, wait = setup_webdriver()
    print('----- First WebDriver Initialized. -----\n')
    
    start_time = time.time()
    i = 1
    j = 1
    while True:
        print('\n\n=======================================')
        print(f'====== STARTING UPDATE CHECK #{i} =======')
        print(f'|| Date & Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ||')
        print('=======================================')

        # Reinitialize WebDriver every few hours
        if time.time() - start_time > REINITIALIZATION_INTERVAL:
            print('---------------------------------------')
            print(f'----- Closing WebDriver #{j} -----')
            print('---------------------------------------')
            # Close the previous WebDriver instance before reinitializing
            if 'driver' in locals():
                driver.quit()
            print(f'----- WebDriver #{j} Closed. -----')

            j += 1
            print('---------------------------------------')
            print(f'----- Reinitializing WebDriver #{j} -----')
            print('---------------------------------------')
            driver, wait = setup_webdriver()
            print(f'----- WebDriver #{j} Reinitialized. -----\n')

            start_time = time.time()

        try:
            login(driver, wait)

        except TimeoutException as e:
            print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print('!!!!!! EXCEPTION: TIMEOUT after trying login() !!!!!!!')
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(f"SIGN IN FAILED -- TimeoutException -- Either the username or password field was not located after 10 seconds: {e}")
            traceback.print_exc()
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')

            screenshot_path = take_screenshot(driver)
            send_email("IRCC Portal Script Error", f"SIGN IN FAILED  after trying login(): TimeoutException occurred: {e}", screenshot_path)
            # send_push_notification("IRCC Portal Script Error", f"TimeoutException occurred: {e}")

            if 'driver' in locals():
                driver.quit()

            sys.exit("\n\n!!! EXITING SCRIPT DUE TO UNHANDLED EXCEPTION !!!\n\n")

        except Exception as e:
            print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print('!!!!!! EXCEPTION: OTHER after trying login() !!!!!!!')
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(f"SIGN IN FAILED -- An error occurred: {e}")
            traceback.print_exc()
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')

            screenshot_path = take_screenshot(driver)
            send_email("IRCC Portal Script Error", f"SIGN IN FAILED after trying login(): An error occurred: {e}", screenshot_path)
            # send_push_notification("IRCC Portal Script Error", f"An error occurred: {e}")

            if 'driver' in locals():
                driver.quit()

            sys.exit("\n\n!!! EXITING SCRIPT DUE TO UNHANDLED EXCEPTION !!!\n\n")


        try:
            check_for_updates(driver, wait)

        except TimeoutException as e:
            print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print('!!!!!! EXCEPTION: TIMEOUT after trying check_for_updates() !!!!!!!')
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(f"UPDATE CHECK FAILED -- TimeoutException -- The \'Updated\' field wasn't located after 10 seconds: {e}")
            traceback.print_exc()
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')

            screenshot_path = take_screenshot(driver)
            send_email("IRCC Portal Script Error", f"CHECKING FOR UPDATE FAILED after trying check_for_updates(): TimeoutException occurred: {e}", screenshot_path)
            # send_push_notification("IRCC Portal Script Error", f"TimeoutException occurred: {e}")

            if 'driver' in locals():
                driver.quit()

            sys.exit("\n\n!!! EXITING SCRIPT DUE TO UNHANDLED EXCEPTION !!!\n\n")

        except Exception as e:
            print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print('!!!!!! EXCEPTION: OTHER after trying check_for_updates() !!!!!!!')
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(f"UPDATE CHECK FAILED -- An error occurred: {e}")
            traceback.print_exc()
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')

            screenshot_path = take_screenshot(driver)
            send_email("IRCC Portal Script Error", f"UPDATE CHECK FAILED after trying check_for_updates(): An error occurred: {e}", screenshot_path)
            # send_push_notification("IRCC Portal Script Error", f"An error occurred: {e}")

            if 'driver' in locals():
                driver.quit()

            sys.exit("\n\n!!! EXITING SCRIPT DUE TO UNHANDLED EXCEPTION !!!\n\n")
            
        finally:
            print('\n=======================================')
            print(f'|| Date & Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ||')
            print('=======================================')
            print(f'===== ENDING UPDATE CHECK #{i} ======')
            print('=======================================')
            print(f"*zzz* Sleeping for {CHECK_INTERVAL_SECONDS} seconds before checking again. *zzz*")
            print('=======================================')
            print('=======================================\n\n\n')

            sys.stdout.flush()
            time.sleep(CHECK_INTERVAL_SECONDS)  # sleep for CHECK_INTERVAL_SECONDS seconds

        i += 1

    # print('\n\n=======================================')
    # print(f'|| Date & Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ||')
    # print('=======================================')
    # print('===== IRCC UPDATE SCRIPT END ======')
    # print('=======================================')
    # print('=======================================')
    # print('=======================================\n\n')


if __name__ == "__main__":
    main()
