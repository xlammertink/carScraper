# Poolcar scraper

This script is created to get alerted whenever new cars are published on the poolsite. It will check which cars are newly published, downloads the details of the car and notifies via e-mail and Telegram.

## Configuring variables

The script uses a few variables to make everything work. Please update the following variables:

- `loginName`: The username to log in on the portal
- `loginPassword`: The password to log in on the portal
- `telegramToken`: The token to communicate with the Telegram API
- `telegramChatId`: The chat id where updates should be sent
- `emailFrom`: The (GMail) e-mailaddress used to send an e-mail
- `emailTo`: The email addresses that should receive a notification e-mail
- `emailPassword`: The app password of your e-mailaddress used to send an e-mail using SMTP

## Python requirements

The script is created for Python 3 and uses Selenium. It is recommended to create a virtual environment in which the Python requirements are installed.

```
# Setup the virtual environment
python3 -m venv venvScraper

# Activate the virtual environment
source venvScraper/bin/activate

# Install required packages
pip3 install pip --upgrade
pip3 install -r requirements.txt
```

## Running the script

Running the script is as easy as running the command: `python3 carScraper.py`.

In case the script is throwing errors, consider commenting out the Selenium `--headless` argument to see what's going wrong.

## Systemd

Systemd unit files have been added to the systemd folder. There are 3 files:

- `carscraper.sh`: A script that activates the virtual environment and runs the script.
- `carscraper.service`: The systemd unit file that executes the previously mentioned script.
- `carscraper.timer`: The systemd unit file that ensures that the service runs every 5 minutes.

If needed, update the paths and username in the bash script and service file. Copy the `.service` and `.timer` file to `~/.config/systemd/user` or `/usr/share/systemd` and start the service.
