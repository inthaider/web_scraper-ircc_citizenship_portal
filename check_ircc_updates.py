"""
This script checks for updates on the IRCC portal and sends a notification 
if there is an update.

(Note: The ".. code-block:: bash" is used to format the code in the 
documentation. It is not part of the code itself.)

Examples
--------
To run the script, use the following command:

.. code-block:: bash

    $ python check_ircc_updates.py

To run the script in the background:

.. code-block:: bash

    $ nohup python -u check_ircc_updates.py > output.log &

Here, `-u` forces the output to be unbuffered, `> output.log` redirects the 
output to the log file, and `&` runs the process in the background.

To run the script with output in the terminal and log file in a `screen` 
session:

.. code-block:: bash

    $ python -u check_ircc_updates.py | tee output.log

Here, `| tee output.log` redirects the output to the log file. The `|` symbol 
is a pipe that passes the output of the command on the left as input to the 
command on the right.

To kill the process, follow these steps:

.. code-block:: bash

    $ ps aux | grep 'check_ircc_updates.py' | grep -v grep

This returns a list of matching processes. The column breakdown is as follows:

    USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
    [1]        [2] [3]  [4]    [5]   [6] [7]      [8]  [9]   [10] [11]

[1] USER: User who started the process.
[2] PID: Process ID.
[3] %CPU: CPU usage.
[4] %MEM: Memory usage.
[5] VSZ: Virtual memory usage.
[6] RSS: Physical memory usage.
[7] TTY: Terminal from which process was started.
[8] STAT: Status of the process.
[9] START: Start time of the process.
[10] TIME: Cumulative CPU time.
[11] COMMAND: Command to start the process.

To kill the process, get the PID and use the following command:

.. code-block:: bash

    $ kill -9 <PID>

Functions
---------
setup_webdriver()
    Sets up the Selenium WebDriver.
login(driver, wait)
    Logs in to the IRCC portal.
check_for_updates(driver, wait)
    Checks for updates on the IRCC portal.
take_screenshot(driver, update=False)
    Takes a screenshot of the IRCC portal.
send_notification(updated_date, update, screenshot_path)
    Sends a notification via email and/or push.
send_email(subject, body, screenshot_path=None)
    Sends an email notification.
send_push_notification(title, message)
    Sends a push notification.
main()
    The main function; runs the script.

Notes
-----
This script uses Selenium to automate a web browser. The script uses the 
Safari WebDriver, but you can use any WebDriver. Download the WebDriver for 
your browser here: https://www.selenium.dev/downloads/

"""

import datetime
import json
import logging
import os
import smtplib
import sys
import time
import traceback
from contextlib import contextmanager
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from purge_screenshots import purge_old_screenshots as pshots

# Define logging configuration that'll be used to log
# messages to the log file and the terminal.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('ircc_portal.log'),
        logging.StreamHandler()
    ]
)

# Open the config.json file with the login credentials
# and other private configuration settings.
with open('config.json') as f:
    config = json.load(f)

#
# Set the configuration settings from the config file
# These are private settings that should not be shared
# with others, hence they are being read from a config
# file instead of being hard-coded in the script.
#
USERNAME_IRCC = config['USERNAME_IRCC']
PASSWORD_IRCC = config['PASSWORD_IRCC']
EMAIL_SERVER = config['EMAIL_SERVER']
EMAIL_PORT = config['EMAIL_PORT']
EMAIL_ADDRESS = config['EMAIL_ADDRESS']
EMAIL_PASSWORD = config['EMAIL_PASSWORD']
PUSH_USER = config['PUSH_USER']     # Optional
PUSH_TOKEN = config['PUSH_TOKEN']       # Optional

#
# Set the configuration settings that are not private
#
LOGIN_URL = "https://tracker-suivi.apps.cic.gc.ca/en/login"
DASHBOARD_URL = "https://tracker-suivi.apps.cic.gc.ca/en/dashboard"

# This is the interval at which the script will check for updates:
CHECK_INTERVAL_SECONDS = 1 * 60 * 60        # 1 hr * 60 min/hr * 60 sec/min
# Interval at which the WebDriver will be reinitialized:
#   I've set it to 0.5 of the check interval because I think it needs to 
#   be reinitialized before every check. Otherwise, it might
#   get stuck on the login page.
REINITIALIZATION_INTERVAL = CHECK_INTERVAL_SECONDS / 2
LAST_UPDATED_FILE = "last_updated.txt"      # File to store last updated date
SCREENSHOTS_DIR = "screenshots"     # Dir to store screenshots
PURGE_SCREENSHOTS = True        # Whether to purge old screenshots
NUM_SCREENSHOTS_TO_KEEP = 1     # No. of screenshots to keep if purging

@contextmanager
def setup_webdriver():
    """Set up the Selenium WebDriver and return it as a context manager.

    Parameters
    ----------
    None

    Returns
    -------
    driver : selenium.webdriver
        The WebDriver object.
    wait : selenium.webdriver.support.wait.WebDriverWait
        The WebDriverWait object.

    Notes
    -----
    The WebDriver is set up as a context manager so that it is automatically
    closed when the script is finished running.

    Context managers are used with the `with` statement. The `yield` statement
    is used to return the WebDriver object. The `finally` statement is used to
    close the WebDriver. 
    
    Context managers are useful for setting up and
    tearing down resources. They're different from functions because they
    automatically clean up after themselves. For more information, see:
    https://book.pythontips.com/en/latest/context_managers.html
    """
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")       # Disable the automation control warning
    options.add_argument("--headless")  # Run in headless mode

    driver = webdriver.Chrome(options=options)  # initialize the WebDriver
    driver.maximize_window()  # maximize the window
    wait = WebDriverWait(driver, 10)

    try:
        yield driver, wait
    finally:
        driver.quit()
    # return driver, wait

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
    username_field.send_keys(USERNAME_IRCC)

    # Wait for the password field to be located and input password
    password_field = wait.until(EC.element_to_be_clickable((By.ID, "password")))
    # Check if the password field is selected
    # if driver.switch_to.active_element != password_field:
    #     # If not, click the password field to select it
    #     password_field.click()
    password_field.send_keys(PASSWORD_IRCC)
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

        server = smtplib.SMTP_SSL(EMAIL_SERVER, EMAIL_PORT)       # This line of code creates a secure SSL context and creates an SMTP object.
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
        "token": PUSH_TOKEN,
        "user": PUSH_USER,
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
    logging.info('=======================================')
    logging.info('=======================================')
    logging.info('=======================================')
    logging.info('===== IRCC PORTAL UPDATE CHECKER ======')
    logging.info('=======================================')
    logging.info(f'|| Date & Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ||')
    logging.info('=======================================')
    logging.info('----- Initial WebDriver Setup... -----')
    logging.info('=======================================')

    # Initial WebDriver setup
    with setup_webdriver() as (driver, wait):
        logging.info('----- First WebDriver Initialized. -----')

        start_time = time.time()
        i = 1
        j = 1
        while True:
            logging.info('=======================================')
            logging.info(f'====== STARTING UPDATE CHECK #{i} =======')
            logging.info(f'|| Date & Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ||')
            logging.info('=======================================')

            # Reinitialize WebDriver every few hours
            if time.time() - start_time > REINITIALIZATION_INTERVAL:
                logging.info('---------------------------------------')
                logging.info(f'----- Closing WebDriver #{j} -----')
                logging.info('---------------------------------------')
                
                # Close the previous WebDriver instance before reinitializing
                if 'driver' in locals():
                    driver.quit()
                logging.info(f'----- WebDriver #{j} Closed. -----')

                j += 1
                logging.info('---------------------------------------')
                logging.info(f'----- Reinitializing WebDriver #{j} -----')
                logging.info('---------------------------------------')
                
                # Reinitialize WebDriver
                with setup_webdriver() as (driver, wait):
                    logging.info(f'----- WebDriver #{j} Reinitialized. -----\n')

                start_time = time.time()

            try:
                login(driver, wait)

            except TimeoutException as e:
                logging.error('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logging.error('!!!!!! EXCEPTION: TIMEOUT after trying login() !!!!!!!')
                logging.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logging.error('SIGN IN FAILED -- TimeoutException -- Either the username or password field was not located after 10 seconds')
                logging.exception(e)
                logging.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

                screenshot_path = take_screenshot(driver)
                send_email("IRCC Portal Script Error", f"SIGN IN FAILED after trying login() -- TimeoutException occurred: {e}", screenshot_path)

                sys.stdout.flush()      # flush stdout buffer
                sys.exit("\n\n!!! EXITING SCRIPT DUE TO UNHANDLED EXCEPTION !!!\n !!! TimeoutException in login() !!!\n\n")

            except Exception as e:
                logging.error('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logging.error('!!!!!! EXCEPTION: OTHER after trying login() !!!!!!!')
                logging.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logging.error('SIGN IN FAILED -- An error occurred')
                logging.exception(e)
                logging.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

                screenshot_path = take_screenshot(driver)
                send_email("IRCC Portal Script Error", f"SIGN IN FAILED after trying login() -- An error occurred: {e}", screenshot_path)

                sys.stdout.flush()      # flush stdout buffer
                sys.exit("\n\n!!! EXITING SCRIPT DUE TO UNHANDLED EXCEPTION !!!\n !!! Exception in login() !!!\n\n")


            try:
                check_for_updates(driver, wait)

            except TimeoutException as e:
                ('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logging.error('!!!!!! EXCEPTION: TIMEOUT after trying login() !!!!!!!')
                logging.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logging.error("UPDATE CHECK FAILED -- TimeoutException -- The 'Updated' field wasn't located after 10 seconds")
                logging.exception(e)
                logging.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

                screenshot_path = take_screenshot(driver)
                send_email("IRCC Portal Script Error", f"CHECKING FOR UPDATE FAILED after trying check_for_updates() -- TimeoutException occurred: {e}", screenshot_path)

                sys.stdout.flush()      # flush stdout buffer
                sys.exit("\n\n!!! EXITING SCRIPT DUE TO UNHANDLED EXCEPTION !!!\n !!! TimeoutException in check_for_updates() !!!\n\n")

            except Exception as e:
                logging.error('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logging.error('!!!!!! EXCEPTION: OTHER after trying login() !!!!!!!')
                logging.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logging.error('UPDATE CHECK FAILED -- An error occurred')
                logging.exception(e)
                ('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

                screenshot_path = take_screenshot(driver)
                send_email("IRCC Portal Script Error", f"UPDATE CHECK FAILED after trying check_for_updates() -- An error occurred: {e}", screenshot_path)

                sys.stdout.flush()      # flush stdout buffer
                sys.exit("\n\n!!! EXITING SCRIPT DUE TO UNHANDLED EXCEPTION !!!\n !!! Exception in check_for_updates() !!!\n\n")
                
            finally:
                # Purge old screenshots if PURGE_SCREENSHOTS is True else do nothing.
                pshots(SCREENSHOTS_DIR, NUM_SCREENSHOTS_TO_KEEP) if PURGE_SCREENSHOTS else None

                logging.info('=======================================')
                logging.info(f'|| Date & Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ||')
                logging.info(f'===== ENDING UPDATE CHECK #{i} ======')
                logging.info('=======================================')
                logging.info(f"*zzz* Sleeping for {CHECK_INTERVAL_SECONDS} seconds before checking again. *zzz*")
                logging.info('=======================================')
                logging.info('=======================================\n\n\n')

                sys.stdout.flush()      # flush stdout buffer
                time.sleep(CHECK_INTERVAL_SECONDS)  # sleep for CHECK_INTERVAL_SECONDS seconds

            i += 1

if __name__ == "__main__":
    main()
