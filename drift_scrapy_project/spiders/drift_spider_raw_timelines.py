import scrapy
import json
import signal
from os import makedirs, listdir
from os.path import exists, dirname, join
from scrapy_selenium import SeleniumRequest
from scrapy.utils.project import get_project_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from drift_scrapy_project.items import DriftUserActivity

class DriftSpiderRawTimelines(scrapy.Spider):
    name = 'driftSpiderRawTimelines'
    allowed_domains = ['drift.com']
    _cookies = ''
    bearerAuthToken = ''
    userCount = 0
    startUserId = ''
    spiderStopped = False

    custom_settings = {
        'START_WITH_USER_ID': ''
    }

    def __init__(self, startWithUserId="", *args, **kwargs):
        super(DriftSpiderRawTimelines, self).__init__(*args, **kwargs)

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
            #url="https://drift.com",
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

        self.rawVisitorsJSON = []
        # Flow - open each file in raw_visitors
        for filename in listdir(self.projectSettings["RAW_OUTPUT_FOLDER"]):
            if "raw_visitor_activity" in filename:
                with open(join(self.projectSettings["RAW_OUTPUT_FOLDER"], filename), 'r') as f:
                    fileJSON = json.load(f)
                    self.rawVisitorsJSON = self.rawVisitorsJSON + fileJSON
        # Enumerate the IDs
        for visitorRecord in self.rawVisitorsJSON:
            #Simple manual restart logic - pull last scraped id from log file and put in settings or commandline arg
            if self.spiderStopped:
                return
            if self.restartOnUserId:
                if self.startUserId == str(visitorRecord['id']):
                    self.restartOnUserId = False
            else:    
                yield scrapy.Request(url="https://customer.api.drift.com/end_users/"+str(visitorRecord['id'])+"/timeline?size=999&offset=0&resolveMaster=false&filter=EVENT",
                    callback=self.parse_end_user,
                    method='GET',
                    headers={
                        "authorization": "Bearer " + self.bearerAuthToken
                    },
                    cb_kwargs=dict(endUserID=str(visitorRecord['id']))
                )

    def parse_end_user(self, response, endUserID):
        end_user_response_json = json.loads(response.text)
        end_user_item = DriftUserActivity(driftUserActivityJSON = end_user_response_json)
        self.userCount = self.userCount + 1
        self.logger.info("Scraped EndUser " + endUserID + " #" + str(self.userCount))
        return end_user_item
  
