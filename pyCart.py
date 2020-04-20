import os
import sys
import argparse
import time
import json
import logging
import time

from os import path
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By

from twilio.rest import Client

class AutomateGroceryDelivery:
    def __init__(self):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--user', action="store")
        parser.add_argument('--password', action="store")
        args = parser.parse_args()
        self.username = args.user
        self.password = args.password

        self.my_mobile = os.environ['USER_MOBILE_NUMBER']
        self.twilio_num = os.environ['TWILIO_MOBILE_NUMBER']
        self.text_content = "Slots Available on Instacart. Order now!"
        self.long_pause = 30
        self.short_pause = 2
        self.page_load_pause = 5

        #Create and configure logger 
        logging.basicConfig(filename="insta_cart.log", 
                            format='%(asctime)s %(message)s', 
                            filemode='w')
        #Creating an object 
        self.logger = logging.getLogger() 
        #Setting the threshold of logger to INFO 
        self.logger.setLevel(logging.INFO)
        
        # This is the right way to source sid and token. Put these an env file and source it in python
        # You *can* put them directly here as well but that is **INSCEURE**
        self.account_sid = os.environ['TWILIO_ACCOUNT_SID']
        self.auth_token = os.environ['TWILIO_AUTH_TOKEN']
        self.cookies_file = 'insta_cart_session_cookies.data'
        self.insta_cart_base_url = 'https://www.instacart.com/'
        self.insta_cart_signin_url = self.insta_cart_base_url
        self.insta_cart_cart_url = self.insta_cart_base_url + 'store/checkout_v3'
        self.driver = webdriver.Chrome(os.environ['WEB_DRIVER_PATH'])  # Optional argument, if not specified will search path.
        self.driver.maximize_window()
        self.cookies_set = False

    def send_sms(self, msg = None):
        # Your Account Sid and Auth Token from twilio.com/console
        self.logger.info("sending sms...")
        
        text_content = self.text_content
        if msg:
            text_content = msg

        client = Client(self.account_sid, self.auth_token)

        client.messages.create(
            to = self.my_mobile, 
            from_ = self.twilio_num,
            body = text_content)

    def login(self, redirect = True):
        # login is called from two places:
        # 1.) initial login
        # 2.) when password is asked again for sign in
        logging.info("logging in...")
        if redirect:
            self.driver.get(self.insta_cart_signin_url)
            time.sleep(self.page_load_pause)
            login_btn = self.driver.find_element_by_xpath('//button[text()="Log in"]') #Proceed to Log In
            login_btn.click()
            self.logger.info("Proceeding to checkout...")
 
        try:
            user_name = self.driver.find_element_by_id('nextgen-authenticate.all.log_in_email')
            user_name.clear()
            user_name.send_keys(self.username)
            time.sleep(self.short_pause) # add delay to stop the captcha kickin
        except:
            pass # sometimes only password is asked so expected that username is not present

        password = self.driver.find_element_by_id('nextgen-authenticate.all.log_in_password')
        password.clear()
        password.send_keys(self.password)

        signin_btn = self.driver.find_element_by_xpath('//button[@type="submit" and text()="Log in"]')
        signin_btn.click()

    def execute(self):

        # login
        self.logger.info("Script ran for the first time. Starting with home page.")
        self.login()
        time.sleep(self.page_load_pause)

        # go to checkout page
        self.logger.info("Proceeding to checkout...")
        self.driver.get(self.insta_cart_cart_url)
        time.sleep(self.short_pause)

        # See if slots available
        slot_available = False
        count = 1
        while (not slot_available):
            self.logger.info("No slots available. Trying again... attempt = " + str(count))

            # see if we landed on proceed to check out page
            # sometimes after many refreshes you are re-directed to the proceed to checkout page again
            # therefore we need to check for it and if so then go to final checkout page again
            try:
                if self.driver.current_url.lower().contains(self.insta_cart_cart_url):
                    pass
                else:
                    # see if password is asked again
                    # if so then enter it
                    try:
                        self.login(redirect = False) # no redirect to login page # we already at the login screen
                    except:
                        self.logger.info("No password asked again... Continuing...")                
            except:
                # do nothing as we are on right page
                pass
                      
            time.sleep(self.long_pause)
            count+=1

            # Check if any slots available. Prime now displays the below msg if that is the case
            try:
                print('checking delivery options')
                delivery_options = self.driver.find_element_by_id('Delivery options')
                if (len(delivery_options.find_elements(By.CSS_SELECTOR, "div")) > 1):
                    slot_available = True
            except:
                # if can't find the confirmation that window is available refresh
                self.driver.refresh()                

        # Delivery slot available! Send sms
        self.send_sms()

a = AutomateGroceryDelivery()
a.execute()