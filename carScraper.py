#!/usr/bin/python3

# This script heavily relies on Selenium
# You can install Selenium using `pip install selenium`
# Selenium Docs: https://selenium-python.readthedocs.io/locating-elements.html

# Import generic libraries
import time # For waiting
import os # For filesystem actions
import re # For regex validation
import requests # For API requests to Telegram

# Import Selenium libraries
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import email libraries
import base64 # To convert images
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Set login variables
loginName = ""
loginPassword = ""

# Set Telegram variables
telegramToken = "" # Create bot via BotFather
telegramChatId = 123456789 # Get chat ID via https://api.telegram.org/bot{{telegramToken}}/getUpdates

# Set email variables
emailFrom = 'youremail@gmail.com'
emailTo = ['abc@example.com', 'test@example.com']
emailPassword = "" # Using app password, which is available after 2FA configuration, via https://myaccount.google.com/apppasswords

class TelegramBot:
    def __init__(self, telegramApiToken, telegramChatId):
        self.apiUrl = "https://api.telegram.org/bot" + telegramApiToken
        self.chatId = telegramChatId
        self.botInfo = requests.get(self.apiUrl + "/getMe").text

    def sendMessage(self, carName):
        requestData = {
            "chat_id" : self.chatId,
            "text" : "New car: " + carName + ". Check https://portal.koopman.nl/PoolSite"
        }
        requests.post(self.apiUrl + "/sendMessage", json = requestData)

    def sendPhoto(self, photoFile):
        requestData = { "chat_id" : self.chatId }
        with open(photoFile, "rb") as f:
            r = requests.post(self.apiUrl + "/sendPhoto", data = requestData, files={"photo": f})

class PoolScraper:
    def __init__(self):
        # Set variables
        self.poolUrl = "https://portal.koopman.nl/PoolSite"
        self.dataDir = "data"
        self.scrapedFile = self.dataDir + "/scraped.txt"

        # Create a (headless) browser instance
        options = webdriver.ChromeOptions()
        options.add_argument('--headless') # Run Chrome in headless mode, will most probably fckup images
        options.add_argument('--window-size=1024,768')
        self.driver = webdriver.Chrome(options=options)

        # Ensure data folder is present
        if not os.path.isdir(self.dataDir):
            os.makedirs(self.dataDir)
        if not os.path.isfile(self.scrapedFile):
            open(self.scrapedFile, 'x').close()

    def login(self, username, password):
        # Go to login page
        self.driver.get(self.poolUrl + "/Login")
        wait = WebDriverWait(self.driver, 10)

        # Enter username
        wait.until(EC.presence_of_element_located((By.ID, 'Input_Email'))).send_keys(username)
        # Enter password
        wait.until(EC.presence_of_element_located((By.ID, 'Input_Password'))).send_keys(password)
        # Log in
        wait.until(EC.presence_of_element_located((By.XPATH, '//button[text()="Login"]'))).send_keys(Keys.RETURN)

        # Wait a little to properly log in
        time.sleep(3)

    def getCarUrls(self):
        # Wait a bit for all cars to be loaded
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'osui-accordion-item')))

        # Get all URLs
        elementUrls = self.driver.find_elements(By.XPATH, "//a[@href]")

        # Build list with URLs of cars
        urls = []
        for element in elementUrls:
            if "VehicleId" in element.get_attribute("href"):
                urls.append(element.get_attribute("href"))

        # Return list
        return urls

    def getId(self, carUrl):
        # Get car ID
        carId = int(carUrl.split('=')[1]) if carUrl.split('=')[1].isdigit() else int(1)
        # Return ID
        return carId

    def getDetails(self, carUrl):
        # Go to car page
        self.driver.get(carUrl)
        wait = WebDriverWait(self.driver, 10)

        # Get data from page
        mainData = wait.until(EC.presence_of_element_located((By.ID, 'b5-Container_VoertuigDetail')))
        itemKey = mainData.find_elements(By.CLASS_NAME, 'item')
        itemValue = mainData.find_elements(By.CLASS_NAME, 'itemvalue')

        # Create object
        carData = {}
        for i in range(len(itemKey)):
            carData.update({itemKey[i].text: itemValue[i].text})

        # Return data
        return carData

    def getDescription(self, carUrl):
        # Go to car page
        self.driver.get(carUrl)
        wait = WebDriverWait(self.driver, 10)

        # Get main data
        leftSide = wait.until(EC.presence_of_element_located((By.ID, 'Container_Images')))
        details = leftSide.find_elements(By.TAG_NAME, 'span')

        # Merge elements
        carData = ""
        for i in details:
            carData += i.text + "\n"
        
        # Return data
        return carData.strip()

    def getData(self, carUrl, carDetails):
        # Set up variable
        carData = {}

        # Get car id
        carId = self.getId(carUrl)
        carData.update({"id": carId})
        
        # Get license plate
        regexLicenseplate = '([A-Z]{1,3}|[0-9]{1,3})-([A-Z]{1,3}|[0-9]{1,3})-([A-Z]{1,3}|[0-9]{1,3})' # Not very accurate, but does the job
        licenseplate = carDetails["Kenteken"] if re.match(regexLicenseplate, carDetails["Kenteken"]) else "AB-CD-01"
        carData.update({"licenseplate": licenseplate})

        # Get car name
        carName = ""
        for item in ["Merk", "Model", "Uitvoering"]:
            if (item in carDetails) and (carDetails[item] != "-"):
                carName += carDetails[item].title() + " "
        carName = carName.strip() if len(carName) > 0 else "Unknown"
        carData.update({"name": carName})

        # Return data
        return carData

    def getImageUrls(self, carUrl):
        # Go to car page
        self.driver.get(carUrl)
        wait = WebDriverWait(self.driver, 10)

        # Get images
        leftSide = wait.until(EC.presence_of_element_located((By.ID, 'Container_Images')))
        carImages = leftSide.find_elements(By.TAG_NAME, 'img')

        # Build list with URLs of images
        urls = []
        for image in carImages:
            urls.append(image.get_attribute("src"))

        # Return list
        return urls

    def downloadImages(self, carImageUrls, carLicenseplate):
        # Download images
        downloadedFiles = []
        for i in range(1, len(carImageUrls)):
            # Go to image
            self.driver.get(carImageUrls[i])
            wait = WebDriverWait(self.driver, 10)

            # Create directory
            carDataDirectory = "data/" + carLicenseplate
            if not os.path.isdir(carDataDirectory):
                os.makedirs(carDataDirectory)

            # Download image
            imgFilename = str(i) + ".png"
            self.driver.save_screenshot(carDataDirectory + "/" + imgFilename)

            # Keep track of downloaded files
            downloadedFiles.append(carDataDirectory + "/" + imgFilename)

        # Return filenames of downloaded files
        return downloadedFiles

    def getProcessed(self):
        # Read scraper file
        with open(self.scrapedFile, "r") as f:
            scrapedCars = f.read().splitlines()

        # Return processed cars
        return scrapedCars

    def confirmProcessed(self, carId):
        # Write car ID to scraper file
        scraperFile = open(self.scrapedFile, "a")
        scraperFile.writelines([str(carId) + "\n"])
        scraperFile.close()

    def close(self):
        self.driver.close()

def sendEmail(carData, carDetails, carDescription, carPhotos):
    # Create email
    email = MIMEMultipart('alternative')

    # Set up email details
    email["Subject"] = "New car available - " + carData["licenseplate"]
    email["From"] = emailFrom
    email["To"] = ', '.join(emailTo)

    # Set email body - plain text
    plainBody = carData["name"] + "\n\n"
    for key, value in carDetails.items():
        plainBody += key + ": " + value + "\n"
    plainBody += "\n" + carDescription
    email.attach(MIMEText(plainBody, 'plain'))

    # Set email body - html
    htmlBody = """
    <html><body>
            <h1> """ + carData["name"] + """</h1>
            <h2>Details</h2>
            <p>
                <table>
    """
    for key, value in carDetails.items():
        htmlBody += "<tr><td>" + key + "</td><td>" + value + "</td></tr>"
    htmlBody += """
                </table>
            </p>
            <h2>Description</h2>
            <p>""" + carDescription.replace("\n", "<br>") + """</p>
            <h2>Photos</h2>
            <p>
    """
    for file in carPhotos:
        with open(file, 'rb') as f:
            photo = base64.b64encode(f.read())
        htmlBody += "<img src='data:image/png;base64," + photo.decode('utf-8') + "'><br>"
    htmlBody += """
            </p>
        </body></html>
    """
    email.attach(MIMEText(htmlBody, 'html'))

    # # Add photos as attachment
    # for file in carPhotos:
    #     with open(file, 'rb') as f:
    #         photo = f.read()
    #     email.add_attachment(photo, maintype='image', subtype='png')

    # Send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(emailFrom, emailPassword)
        server.sendmail(emailFrom, emailTo, email.as_string())


#
# Let the show begin
#

# Set up scraper
scraper = PoolScraper()

# Set up Telegram bot
telegram = TelegramBot(telegramToken, telegramChatId)

# Log in on pool website
scraper.login(loginName, loginPassword)

# Get car URLs
urlList = scraper.getCarUrls()

# For each of the cars
for url in urlList:
    # Get car ID
    carId = scraper.getId(url)

    # Get cars that have been scraped before
    scrapedCars = scraper.getProcessed()

    # Only process cars that have not been scraped before
    if str(carId) not in scrapedCars:

        # Get detail data (right colomn)
        carDetails = scraper.getDetails(url)

        # Get description (left colomn)
        carDescription = scraper.getDescription(url)

        # Confirm information
        carData = scraper.getData(url, carDetails)

        # Download images
        carImageUrls = scraper.getImageUrls(url)
        imageScraper = PoolScraper()
        imageScraper.login(loginName, loginPassword)
        carImages = imageScraper.downloadImages(carImageUrls, carData["licenseplate"])
        imageScraper.close()

        # Notify on Telegram
        telegram.sendMessage(carData["name"])
        telegram.sendPhoto(carImages[0])

        # Send email
        sendEmail(carData, carDetails, carDescription, carImages)

        # Add car to scraped list
        scraper.confirmProcessed(carId)

# # Timeout before script stops running
# sleep = input("Press ENTER to wake up and shut down...")

scraper.close()
