# Automatic IRCC Portal Update Check

This script checks for updates on the IRCC portal and sends a notification if there is an update. It uses Selenium to automate a web browser and sends email and push notifications when updates are available.

## Overview

The IRCC (Immigration, Refugees and Citizenship Canada) portal is used by applicants to check the status of their immigration applications. This script automates the process of checking for updates on the IRCC portal and sends email and push notifications when updates are available.

## Features

- Automates the process of checking for updates on the IRCC portal
- Sends email and push notifications when updates are available
- Uses Selenium to automate a web browser
- Supports multiple notification channels (email and Pushover)

## Installation

1. Clone the repository
2. Install the required dependencies using `pip install -r requirements.txt`
3. Set up the configuration file `config.json` with your login credentials, SMTP server details, and Pushover API details.

## Usage

To run the script, use the following command:

    python check_ircc_updates.py

To run the script in the background, use the following command:

    nohup python check_ircc_updates.py &

If you then want to kill the process, use the following command:

    ps aux | grep check_ircc_updates.py kill -9

## Configuration

The configuration file `config.json` contains the following parameters:

- `USERNAME`: Your IRCC portal username
- `PASSWORD`: Your IRCC portal password
- `SMTP_SERVER`: Your SMTP server address
- `SMTP_PORT`: Your SMTP server port
- `EMAIL_ADDRESS`: Your email address
- `EMAIL_PASSWORD`: Your email password
- `PUSHOVER_USER`: Your Pushover user key
- `PUSHOVER_TOKEN`: Your Pushover API token

## Notifications

The script sends notifications when updates are available on the IRCC portal. It supports two notification channels: email and Pushover.

### Email Notifications

The script sends email notifications using the SMTP protocol. To set up email notifications, you need to provide the following parameters in the `config.json` file:

- `SMTP_SERVER`: Your SMTP server address
- `SMTP_PORT`: Your SMTP server port
- `EMAIL_ADDRESS`: Your email address
- `EMAIL_PASSWORD`: Your email password

### Push Notifications

The script sends push notifications using the Pushover API. To set up push notifications, you need to provide the following parameters in the `config.json` file:

- `PUSHOVER_USER`: Your Pushover user key
- `PUSHOVER_TOKEN`: Your Pushover API token

## Acknowledgements

- [Selenium](https://www.selenium.dev/)
- [Pushover](https://pushover.net/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.