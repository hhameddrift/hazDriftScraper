import scrapy
import json
import csv
import signal
from os import makedirs, listdir
from os.path import exists, dirname, join
from scrapy_selenium import SeleniumRequest
from scrapy.utils.project import get_project_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from drift_scrapy_project.items import DriftAccountUserList

class DriftSpiderDerivedCompanyInfo(scrapy.Spider):
    name = 'driftSpiderDerivedCompanyInfo'
    allowed_domains = ['drift.com']
    _cookies = ''
    bearerAuthToken = ''
    userCount = 0
    startUserId = ''
    spiderStopped = False

    custom_settings = {
        'START_WITH_USER_ID': '11084762040'
    }

    def __init__(self, startWithUserId="", *args, **kwargs):
        super(DriftSpiderDerivedCompanyInfo, self).__init__(*args, **kwargs)

        self.projectSettings = get_project_settings()

        # Date ranges to scrape with API calls
        if startWithUserId != "":
            self.startUserId = startWithUserId
            self.restartOnUserId = True
        else:
            if self.custom_settings['START_WITH_USER_ID'] != "":
                self.startUserId = self.custom_settings['START_WITH_USER_ID']
                self.restartOnUserId = True
            else:
                self.restartOnUserId = False
        signal.signal(signal.SIGINT, self.sigIntHandler)
    
    def sigIntHandler(self, signum, frame):
        self.logger.info('Spider closed:')
        self.spiderStopped = True           

    def start_requests(self):
        yield SeleniumRequest(
            url='https://app.drift.com/live',
            wait_time=120,
            wait_until=EC.title_is('Drift'),
            screenshot=True,
            callback=self.parse,
            dont_filter=True
        )
    
    def parse(self, response):
        # get all cookies - see cookies_dump.json for saved output of this call
        self._cookies = response.request.meta['driver'].get_cookies()
        authToken = response.request.meta['driver'].get_cookie("DrifttAuth")
        self.bearerAuthToken = authToken["value"]
        # TODO: Move the fromTime and toTime to be parameterized so we don't rescrap ALL records in future

        with open('./' + self.settings['OUTPUT_FOLDER'] + '/userPerCompany.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                    #Simple manual restart logic - pull last scraped id from log file and put in settings or commandline arg
                    if self.spiderStopped:
                        return
                    if self.restartOnUserId:
                        if self.startUserId == row[0]:
                            self.restartOnUserId = False
                    else:    
                        yield scrapy.Request(
                            url="https://contacts.api.drift.com/derivation",
                            callback=self.parse_business_details,
                            method='POST',
                            body='''{
                                "endUserId":''' + row[0] + ''',
                                "targets":[1],
                                "allowExternalEnrichment":true,
                                "maxDepth":2}''',
                            headers={
                                "content-type": "application/json",
                                "authorization": "Bearer " + self.bearerAuthToken
                            },
                            cb_kwargs=dict(endUserID=row[0])
                        )

    def parse_business_details(self, response, endUserID):
        company_details_json = json.loads(response.text)
        if 'derivedObjects' in company_details_json:
            if '1' in company_details_json['derivedObjects']:
                company_item = DriftAccountUserList(driftAccountUserListJSON = [company_details_json['derivedObjects']['1']['value']['companyData']])

                self.userCount = self.userCount + 1
                self.logger.info("Scraped Business Info for EndUser " + endUserID + " #" + str(self.userCount))
                return company_item
        return
  
