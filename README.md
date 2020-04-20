# pycart
Monitors for delivery slots and texts when one opens up

Download this repo onto your system (preferably into a separate folder)
Install selenium driver by running
```
pip install -U selenium
```

- Download web-driver
 -- Check your chrome version - open a chrome browser, go to 'Chrome' menu item and click 'About Google Chrome' to get the version
 -- Download the appropriate chromedriver from here https://chromedriver.chromium.org/downloads and unzip into your folder

- Create a free Twilio account here - https://www.twilio.com/

- Configure envVars.sh file with your details


To run the script, 
```
source envVars.sh
python pycart.py --user <username> --password <password>
```
