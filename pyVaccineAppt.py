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
from selenium.webdriver.common.action_chains import ActionChains

from twilio.rest import Client

class VaccineAppointmentFinder:
    def __init__(self):
        self.my_mobile = os.environ['USER_MOBILE_NUMBER']
        self.twilio_num = os.environ['TWILIO_MOBILE_NUMBER']
        self.text_content = "Vaccine appointments available on Walgreens. Book now!"
        self.long_pause = 10
        self.short_pause = 2
        self.page_load_pause = 5

        #Create and configure logger 
        logging.basicConfig(filename="vaccine_appointments.log", 
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
        self.walgreens_base_url = 'https://www.walgreens.com/findcare/vaccination/covid-19?ban=covid_vaccine1_landing_schedule'
        self.location = '55426'
        self.driver = webdriver.Chrome(os.environ['WEB_DRIVER_PATH'])  # Optional argument, if not specified will search path.
        self.driver.maximize_window()

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

    def openFinder(self):
        logging.info("Opening appointment schedules page...")
 
        try:
            self.driver.get(self.walgreens_base_url)
            time.sleep(self.long_pause)

            schedule_appt_btn = self.driver.find_element_by_xpath('//span[text()="Schedule new appointment" and contains(@class, "btn") and contains(@class, "btn__blue")]')
            actions = ActionChains(self.driver)
            actions.move_to_element(schedule_appt_btn).perform()
            schedule_appt_btn.click()
            time.sleep(self.page_load_pause)

            location_field = self.driver.find_element_by_id('inputLocation')
            location_field.clear()
            location_field.send_keys(self.location)

        except:
          logging.error("exception occurred when opening schedules page")

    def execute(self):

        # login
        self.logger.info("Script ran for the first time. Starting with home page.")
        self.openFinder()

        # See if slots available
        slot_available = False
        count = 1
        while (not slot_available):
            self.logger.info("No slots available. Trying again... attempt = " + str(count))

            count+=1

            # Check if any slots available
            try:
                self.logger.info('checking appointment slots availability')
                buttons = self.driver.find_elements_by_tag_name('button')
                for sbtn in buttons:
                  if(sbtn.text == 'Search'):
                    search_button = sbtn
                    break                
                search_button.click()
                time.sleep(self.short_pause)

                delivery_options = self.driver.find_element_by_xpath('//p[contains(@class, "fs16")]')
                if (delivery_options is None):
                    slot_available = True
                    logging.info("Slots are available")
            except:
                # if can't find the confirmation that window is available refresh
                self.logger.info('unable to check')
                #self.driver.refresh()   
                
            if not slot_available:
                logging.info("No slots available. Will check again after half an hour...")
                time.sleep(1800)                # check every half an hour

        # Delivery slot available! Send sms
        self.send_sms()


try:
    a = VaccineAppointmentFinder()
    a.execute()
finally:
    a.driver.quit()
