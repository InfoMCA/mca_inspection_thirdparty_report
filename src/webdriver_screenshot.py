import os
import shutil
import time
import uuid
import logging
from base64 import b64decode

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger()

WAIT_TIME = 5


def save_pdf(driver, filename):
    a = driver.execute_cdp_cmd("Page.printToPDF", {"path": 'html-page.pdf', "format": 'A4'})
    data_bytes = b64decode(a['data'], validate=True)
    if data_bytes[0:4] != b'%PDF':
        raise ValueError('Missing the PDF file signature')
    pdf_file = open(filename + ".pdf", 'wb')
    pdf_file.write(data_bytes)
    pdf_file.close()


class WebDriverScreenshot:
    def __init__(self):
        self._tmp_folder = '/tmp/{}'.format(uuid.uuid4())

        if not os.path.exists(self._tmp_folder):
            os.makedirs(self._tmp_folder)

        if not os.path.exists(self._tmp_folder + '/user-data'):
            os.makedirs(self._tmp_folder + '/user-data')

        if not os.path.exists(self._tmp_folder + '/data-path'):
            os.makedirs(self._tmp_folder + '/data-path')

        if not os.path.exists(self._tmp_folder + '/cache-dir'):
            os.makedirs(self._tmp_folder + '/cache-dir')

    def __get_default_chrome_options(self):
        chrome_options = webdriver.ChromeOptions()

        lambda_options = [
            '--autoplay-policy=user-gesture-required',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-breakpad',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-default-apps',
            '--disable-dev-shm-usage',
            '--disable-domain-reliability',
            '--disable-extensions',
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-notifications',
            '--disable-offer-store-unmasked-wallet-cards',
            '--disable-popup-blocking',
            '--disable-print-preview',
            '--disable-prompt-on-repost',
            '--disable-renderer-backgrounding',
            '--disable-setuid-sandbox',
            '--disable-speech-api',
            '--disable-sync',
            '--disk-cache-size=33554432',
            '--hide-scrollbars',
            '--ignore-gpu-blacklist',
            '--ignore-certificate-errors',
            '--metrics-recording-only',
            '--mute-audio',
            '--no-default-browser-check',
            '--no-first-run',
            '--no-pings',
            '--no-sandbox',
            '--no-zygote',
            '--password-store=basic',
            '--use-gl=swiftshader',
            '--use-mock-keychain',
            '--single-process',
            '--headless']

        #chrome_options.add_argument('--disable-gpu')
        for argument in lambda_options:
            chrome_options.add_argument(argument)
        chrome_options.add_argument('--user-data-dir={}'.format(self._tmp_folder + '/user-data'))
        chrome_options.add_argument('--data-path={}'.format(self._tmp_folder + '/data-path'))
        chrome_options.add_argument('--homedir={}'.format(self._tmp_folder))
        chrome_options.add_argument('--disk-cache-dir={}'.format(self._tmp_folder + '/cache-dir'))

        chrome_options.binary_location = "/opt/bin/chromium"

        return chrome_options

    def __get_correct_height(self, url, width=1280):
        chrome_options = self.__get_default_chrome_options()
        chrome_options.add_argument('--window-size={}x{}'.format(width, 1024))
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get(url)
        height = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight )")
        driver.quit()
        return height

    def save_screenshot(self, url, filename, width=1280, height=None):
        if height is None:
            height = self.__get_correct_height(url, width=width)

        chrome_options = self.__get_default_chrome_options()
        chrome_options.add_argument('--window-size={}x{}'.format(width, height))
        chrome_options.add_argument('--hide-scrollbars')

        driver = webdriver.Chrome(chrome_options=chrome_options)
        logger.info('Using Chromium version: {}'.format(driver.capabilities['browserVersion']))
        driver.get(url)
        driver.save_screenshot(filename)
        driver.quit()

    def save_carfax_report(self, filename, username, password, vin, width=1280):
        chrome_options = self.__get_default_chrome_options()
        chrome_options.add_argument('--window-size={}x{}'.format(width, 4000))
        chrome_options.add_argument('--hide-scrollbars')

        driver = webdriver.Chrome(chrome_options=chrome_options)
        logger.info('Using Chromium version: {}'.format(driver.capabilities['browserVersion']))

        driver.get("http://www.carfaxonline.com/login")
        username_input = driver.find_element_by_id("username")
        password_input = driver.find_element_by_id("password")
        username_input.send_keys(username)
        password_input.send_keys(password)
        login = driver.find_element_by_id("login_button")
        login.click()
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.ID, 'vin')))

        vin_input = driver.find_element_by_id("vin")
        vin_input.send_keys(vin)
        get_report = driver.find_element_by_id("header_run_vhr_button")
        get_report.click()
        time.sleep(5)

        try:
            driver.switch_to.window(driver.window_handles[1])
            title_status = driver.find_element_by_class_name("headerRowIcon").get_attribute("alt")
            logger.info(title_status)
            info = driver.find_elements_by_class_name("wrappingDesc.header-row-text")
            info_list = []
            for item in info:
                logger.info(item.text.replace('\n', ' '))
                info_list.append(item.text.replace('\n', ' '))
            requests.post('https://leadservices.mycarauction.com/leads/' + vin + '/update-carfax-report',
                          json={'info': info_list})
            save_pdf(driver, filename)
            driver.quit()
            return True
        except Exception:
            driver.quit()
            return False

    def save_manheim_report(self, filename, username, password, vin, mileage, grade, color):
        chrome_options = self.__get_default_chrome_options()
        driver = webdriver.Chrome(chrome_options=chrome_options)
        logger.info('Using Chromium version: {}'.format(driver.capabilities['browserVersion']))

        driver.get("https://mmr.manheim.com/?country=US")
        WebDriverWait(driver, WAIT_TIME).until(expected_conditions.presence_of_element_located((By.ID, 'user_username')))

        username_input = driver.find_element_by_id("user_username")
        username_input.send_keys(username)
        password_input = driver.find_element_by_id("user_password")
        password_input.send_keys(password)
        login = driver.find_element_by_id("submit")
        login.click()
        logger.info("Wait for popups")
        try:
            WebDriverWait(driver, WAIT_TIME).until(
                expected_conditions.presence_of_element_located((By.CLASS_NAME, "uiq_close")))
            driver.find_element_by_class_name("uiq_close").click()
        except Exception:
            try:
                WebDriverWait(driver, WAIT_TIME).until(
                    expected_conditions.presence_of_element_located((By.CLASS_NAME, "useriq-cancel-link")))
                driver.find_element_by_class_name("useriq-cancel-link").click()
            except Exception:
                pass

        logger.info("Wait for VIN")

        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.ID, 'vinText')))
        vin_input = driver.find_element_by_id("vinText")
        vin_input.send_keys(vin)
        vin_input.send_keys(Keys.RETURN)
        logger.info("Wait for PopUps")
        try:
            WebDriverWait(driver, WAIT_TIME).until(
                expected_conditions.presence_of_element_located((By.CLASS_NAME, "useriq-cancel-link")))
            driver.find_element_by_class_name("useriq-cancel-link").click()
            time.sleep(WAIT_TIME)
        except Exception:
            pass
        try:
            WebDriverWait(driver, WAIT_TIME).until(
                expected_conditions.presence_of_element_located((By.CLASS_NAME, "icon-cross")))
            driver.find_element_by_class_name("icon-cross").click()
            time.sleep(WAIT_TIME)
        except Exception:
            pass

        logger.info("Fill info")
        try:
            mileage_input = driver.find_element_by_id("Odometer")
            mileage_input.send_keys(mileage)
            region = driver.find_element_by_id("Region")
            region.send_keys("West Coast")
            grade_input = driver.find_element_by_id("Grade")
            grade_input.send_keys(grade)
            color_input = driver.find_element_by_id("Ext Color")
            color_input.send_keys(color)
            for button in driver.find_elements_by_tag_name("Button"):
                if str(button.text) == "View All":
                    button.click()
            save_pdf(driver, filename)
            driver.quit()
            return True
        except Exception as e:
            logger.error("Error " + str(e))
            driver.quit()
            return False

    def save_autoniq_report(self, filename, username, password, vin, width=640):
        chrome_options = self.__get_default_chrome_options()
        chrome_options.add_argument('--window-size={}x{}'.format(width, 9600))
        chrome_options.add_argument('--hide-scrollbars')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        logger.info('Using Chromium version: {}'.format(driver.capabilities['browserVersion']))

        driver.get("https://www.autoniq.com/app")
        WebDriverWait(driver, WAIT_TIME).until(expected_conditions.presence_of_element_located((By.ID, 'input-username-app')))

        username_input = driver.find_element_by_id("input-username-app")
        username_input.send_keys(username)
        password_input = driver.find_element_by_id("input-password-app")
        password_input.send_keys(password)
        login = driver.find_element_by_id("login-button-app")
        login.click()
        time.sleep(5)
        for item in driver.find_elements_by_tag_name("img"):
            if item.get_attribute("alt") == 'Price Evaluator':
                item.click()
                break
        for item in driver.find_elements_by_tag_name("input"):
            if item.get_attribute("placeholder") == 'Enter VIN':
                item.send_keys(vin)
                break
        for button in driver.find_elements_by_tag_name("button"):
            if button.text == 'Search':
                button.click()
                break
        time.sleep(2)
        for button in driver.find_elements_by_tag_name("button"):
            if button.text == 'Full Report':
                button.click()
                break
        time.sleep(10)

        driver.save_screenshot(filename + ".png")
        driver.quit()

    def get_carfax_highlight(self, username, password, vin, width=1280):
        chrome_options = self.__get_default_chrome_options()
        chrome_options.add_argument('--window-size={}x{}'.format(width, 4000))
        chrome_options.add_argument('--hide-scrollbars')

        driver = webdriver.Chrome(chrome_options=chrome_options)
        logger.info('Using Chromium version: {}'.format(driver.capabilities['browserVersion']))

        driver.get("http://www.carfaxonline.com/login")
        username_input = driver.find_element_by_id("username")
        password_input = driver.find_element_by_id("password")
        username_input.send_keys(username)
        password_input.send_keys(password)
        login = driver.find_element_by_id("login_button")
        login.click()
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.ID, 'vin')))

        vin_input = driver.find_element_by_id("vin")
        vin_input.send_keys(vin)
        get_report = driver.find_element_by_id("header_run_vhr_button")
        get_report.click()
        time.sleep(5)
        info_list = []

        try:
            driver.switch_to.window(driver.window_handles[1])
            title_status = driver.find_element_by_class_name("headerRowIcon").get_attribute("alt")
            logger.info(title_status)
            info = driver.find_elements_by_class_name("wrappingDesc.header-row-text")
            for item in info:
                logger.info(item.text.replace('\n', ' '))
                info_list.append(item.text.replace('\n', ' '))
            driver.quit()
        except Exception:
            driver.quit()
        return info_list

    def close(self):
        # Remove specific tmp dir of this "run"
        shutil.rmtree(self._tmp_folder)