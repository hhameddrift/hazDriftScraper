This is a private api scraper to pull user details from app.drift.com

You will need to setup scrapy.

---Install Steps---
* Recommended path is to install anaconda and then follow scrapy instructions to install it in a conda environment.

* Then run "pip install -r requirements.txt" to install the dependencies

* Download the approprite ChromeDriver for Selenium from https://chromedriver.chromium.org/downloads
Get the same version as your current version of Chrome (Help-> About Google Chrome)

* Place the ChromeDriver executable in the root folder of this project alongside scrapy.cfg

* Edit 'SELENIUM_DRIVER_ARGUMENTS' in settings.py to point to your Chrome profile directory

---Run the scraper---

scrapy crawl driftSpider

The scraper will launch a chrome browser - login to drift with your credentials, then navigate to the Activity->All Accounts page, and click on the "Accounts" tab at top right - the crawler will then start automatically.  leave the browser window open until the crawler completes (there will be no visible activity in the browser window after loading the accounts page, it is running backend api crawls)