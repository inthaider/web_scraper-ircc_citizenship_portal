# IRCC Citizenship Update Checker

This project contains a Python script (`check_ircc_updates.py`) that checks for updates on the IRCC (Immigration, Refugees and Citizenship Canada) portal and sends a notification if there is an update. The script is designed to be run constantly in the background. It checks for updates at a specified interval, and if there is an update, it sends a notification via email and/or push. Note that push notifications setup isn't functional yet, I'm still working on it.

## Requirements

This script requires Python 3.7 or above. Some but not all necessary dependencies are listed in the `requirements.txt` file. You can install these dependencies using pip or Conda:

```bash
pip install -r requirements.txt
```

## Usage

1. Clone this repository to your local machine:

```bash
git clone https://github.com/yourusername/ircc-citizenship.git
```

2. Install the necessary Python dependencies (see above).

3. Rename `config_private.example.json` to `config_private.json`.

4. Modify `config_private.json` to include your personal information:

```json
{
  "ircc_account": {
    "username": "<YOUR_IRCC_USERNAME>",
    "password": "<YOUR_IRCC_PASSWORD>"
  },
  "email": {
    "sender": "<SENDER_EMAIL_ADDRESS>",
    "password": "<SENDER_EMAIL_PASSWORD>",
    "receiver": "<RECEIVER_EMAIL_ADDRESS>"
  },
  "pushover": {
    "api_token": "<PUSHOVER_API_TOKEN>",
    "user_key": "<PUSHOVER_USER_KEY>"
  }
}
```

5. Run the script:

```bash
python check_ircc_updates.py
```

You can also run the script in the background:

```bash
nohup python -u check_ircc_updates.py > output.log &
```

Or in a `screen` session:

```bash
python -u check_ircc_updates.py | tee output.log
```

6. To stop the script, first find the process ID (PID) using this command:

```bash
ps aux | grep 'check_ircc_updates.py' | grep -v grep
```

Then kill the process using the PID:

```bash
kill -9 <PID>
```

## How it Works

When run, `check_ircc_updates.py` uses Selenium WebDriver to log in to the IRCC portal, check for updates, take a screenshot, and send a notification if there is an update. The script logs in using the username and password specified in `config_private.json`, and it sends notifications using the email and Pushover credentials specified in `config_private.json`.

The script also generates several files:

* `output.log` contains the script's console output.
* `last_updated.txt` contains the date and time of the last update.
* `screenshots/` contains screenshots of the IRCC portal.

These files are not tracked by Git.

## Purging Screenshots

The `purge_screenshots.py` script can be used to remove old screenshots from the `screenshots/` directory.

## Note on Selenium WebDriver

This script uses the Safari WebDriver by default, but you can use any WebDriver by specifying it in `config_public.json`. You can download the WebDriver for your browser from the [Selenium downloads page](https://www.selenium.dev/downloads/).

Please ensure that the WebDriver binary is in the PATH of your operating system. As of Selenium 4.6.0, the Selenium bindings will automatically configure the browser drivers for Chrome, Firefox, and Edge if they are not present on the PATH using Selenium Manager.

---

This README.md file is a guide to help any person who would like to use this project/script to check for updates on their IRCC citizenship portal. Please ensure to follow the instructions as given to set up

# IRCC Citizenship Checker

This project checks for updates on the IRCC citizenship portal and sends a notification if there is an update. The script is designed to be run constantly in the background, checking for updates at a specified interval. If there is an update, it will send a notification via email and/or push.

## Getting Started

Follow these instructions to get the project up and running.

### Prerequisites

You will need the following:

- Python 3.6 or above
- A Selenium WebDriver, which automates a web browser (download the WebDriver for your browser [here](https://www.selenium.dev/downloads/))
- The Selenium Python library (install it by running `pip install selenium`)
- The Selenium Manager tool for managing browser drivers【108†source】【149†source】
- Other dependencies specified in `requirements.txt` (install them by running `pip install -r requirements.txt`)

### Configuration

1. Rename `config_private.example.json` to `config_private.json`.
2. Edit `config_private.json` to add your information. It should look something like this:

```json
{
    "email": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "sender@gmail.com",
        "sender_password": "password",
        "receiver_email": "receiver@gmail.com"
    },
    "pushover": {
        "user_key": "userkey",
        "api_token": "apitoken"
    },
    "ircc": {
        "username": "username",
        "password": "password"
    },
    "check_interval": 60
}
```

- The `email` section contains the SMTP server and port for sending the email, as well as the sender's and receiver's email addresses and the sender's password.
- The `pushover` section contains the user key and API token for sending push notifications.
- The `ircc` section contains the username and password for logging in to the IRCC portal.
- The `check_interval` is the time interval (in minutes) at which the script will check for updates.

The `config_private.json` file is ignored by Git, so your sensitive information will not be tracked.

### Usage

You can run the script using the following commands:

- To run the script:

```bash
$ python check_ircc_updates.py
```

- To run the script in the background:

```bash
$ nohup python -u check_ircc_updates.py > output.log &
```

Here, `-u` forces the output to be unbuffered, `> output.log` redirects the output to the log file, and `&` runs the process in the background.

- To run the script with output in the terminal and log file in a `screen` session:

```bash
$ python -u check_ircc_updates.py | tee output.log
```

Here, `| tee output.log` redirects the output to the log file. The `|` symbol is a pipe that passes the output of the command on the left as input to the command on the right.

### Stopping the Script

To kill the process, follow these steps:

1. List matching processes:

```bash
$ ps aux | grep 'check_ircc_updates.py' | grep -v grep
```

This returns a list of matching processes. The PID (Process ID) is the number in the second column.

2. Kill the process:

```bash
$ kill -9 <PID>
```

Replace `<PID>` with the PID of the process.

### Screenshots

The script will take screenshots of the IRCC portal and save them in the `screenshots` directory. The screenshots are named according to the date