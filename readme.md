This is a private api scraper to pull user details from app.drift.com

You will need to setup scrapy.

## Install Steps ##
* Recommended path is to install anaconda and then follow scrapy instructions to install it in a conda environment.

First after environment creation, activate your new environment and from a terminal prompt in that environment run

> `conda install -c conda-forge scrapy`

* Then to install the dependencies, run

> `pip install -r requirements.txt` 



* Download the approprite ChromeDriver for Selenium from https://chromedriver.chromium.org/downloads
Get the same version as your current version of Chrome (Help-> About Google Chrome)

* Place the ChromeDriver executable in the root folder of this project alongside scrapy.cfg

* Edit `'SELENIUM_DRIVER_ARGUMENTS'` in `settings.py` to point to your Chrome profile directory

## Run the scraper ##

> `scrapy crawl driftSpider`

The scraper will launch a chrome browser - login to drift with your credentials, then navigate to the Activity->All Accounts page, and click on the "Accounts" tab at top right - the crawler will then start automatically.  leave the browser window open until the crawler completes (there will be no visible activity in the browser window after loading the accounts page, it is running backend api crawls)

There is very little error handling code and the scrapers run in parallel, async operation.  

## There are 4 scrapers ##

### driftSpider ### 
> `scrapy crawl driftSpider` 

Will get accounts, users, and those user's timelines (activities) for explicitly defined accounts
    This spider creates 3 files in `OUTPUT_FOLDER` (configured in `settings.py)

* `accounts.json`
* `account_users.json`
* `end_user_activity.json`

### driftSpiderRaw ### 
> `scrapy crawl driftSpiderRaw -a startDate=1/1/2020 -a endDate=1/5/2020`

* driftSpiderRaw will get *all* site visitors for a given date range.

* You can set the data range in the custom_config in the spider itself, or on the commandline:
        

    
* This spider may generate very large files.  It is recommended to start with small date ranges first (1 day)

* It will generate a file in the form 
`raw_visitor_activity_1-1-2020_to_1-5-2020.json` in `RAW_OUTPUT_FOLDER` (configured in `settings.py`)

### driftSpiderRawTimelines ### 

> `scrapy crawl driftSpiderRawTimelines`

* Gets all visitor timelines (activities) that were    generated from driftSpiderRaw in `RAW_OUTPUT_FOLDER`

* This scraper is dependent on at least 1 output file being generated from the Raw scraper.

* It will crawl all files in `RAW_OUTPUT_FOLDER`

* It will generate `end_user_activity.json` in `RAW_OUTPUT_FOLDER`

* If you need to break execution of this script, you can restart at a specific userID with
        
> `scrapy crawl driftSpiderRawTimelines -a startWithUserId=XXXXXXXXXXXXXX`

* You can find the last user ID from the output logs (log.txt) - but due to async nature of program
        it will not be sequential and may require some log hunting to find the exactly last processed ID

### driftSpiderDerivedCompanyInfo ### 

> `scrapy crawl driftSpiderDerivedCompanyInfo`

* driftSpiderDerivedCompanyInfo gets all the supplementary company data available for a given CSV of userIDs.

* It looks for `OUTPUT_FOLDER` / `userPerCompany.csv` - This csv should be a single column with no headers of unique userIDs.
    
* You'll need to manually get a distinct userID list from driftSpiderRaw output files to create this CSV list.

* It will generate `raw_companies.json` in `OUTPUT_FOLDER`

* If you need to break execution of this script, you can restart at a specific userID with

> `scrapy crawl driftSpiderDerivedCompanyInfo -a startWithUserId=XXXXXXXXXXXXXX`

* You can find the last user ID from the output logs (`log.txt`) - but due to async nature of program
        it will not be sequential and may require some log hunting to find the exactly last processed ID


