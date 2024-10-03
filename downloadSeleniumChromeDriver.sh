#!/bin/bash
#
# You can use this script if you'd like to to download the chrome driver yourself
#

echo "Get latest version from API"
ChromeVersion="$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE)"

echo "Set download URL prefix and suffix"
ChromeDownloadPrefix="https://chromedriver.storage.googleapis.com/"
ChromeDownloadSuffix="/chromedriver_linux64.zip"

echo "Construct download URL"
ChromeDownloadUrl="$ChromeDownloadPrefix"
ChromeDownloadUrl+="$ChromeVersion"
ChromeDownloadUrl+="$ChromeDownloadSuffix"

echo "Downloading driver"
curl -s $ChromeDownloadUrl -o chromedriver_linux64.zip

echo "Extracting driver"
unzip -qq chromedriver_linux64.zip

echo "Done!"
