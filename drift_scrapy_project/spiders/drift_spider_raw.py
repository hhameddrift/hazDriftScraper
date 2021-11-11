import scrapy
import json
import time
import datetime
from os import makedirs
from os.path import exists, dirname
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from drift_scrapy_project.items import DriftRawVisitorActivity

class DriftSpiderRaw(scrapy.Spider):
    name = 'driftSpiderRaw'
    allowed_domains = ['drift.com']
    _cookies = ''
    bearerAuthToken = ''
    userCount = 0
    companyCount = 0

    custom_settings = {
        'START_DATE': '8/1/2021',
        'END_DATE': '8/1/2021'
    }

    def __init__(self, startDate="", endDate="", *args, **kwargs):
        super(DriftSpiderRaw, self).__init__(*args, **kwargs)
        # Date ranges to scrape with API calls
        if startDate != "":
            self.custom_settings['START_DATE'] = startDate
        if endDate != "":
            self.custom_settings['END_DATE']  = endDate
        #makes a timestamp at the beginning of the beginning day
        self.fromTimeStamp = int(time.mktime(datetime.datetime.strptime(self.custom_settings['START_DATE'], "%m/%d/%Y").timetuple())) * 1000
        #makes a timestamp at the very end of the last day
        self.toTimeStamp = int(time.mktime(datetime.datetime.combine(datetime.datetime.strptime(self.custom_settings['END_DATE'], "%m/%d/%Y"), datetime.time.max).timetuple())) * 1000

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

        # need to break down the calls into X hour chunks (4) - to microsecond timestamp Drift uses
        requestInterval = 4 * 60 * 60 * 1000
        for startTime in range(self.fromTimeStamp, self.toTimeStamp, requestInterval):
            if startTime + requestInterval > self.toTimeStamp:
                endInterval = self.toTimeStamp
            else:
                endInterval = startTime + requestInterval

            yield scrapy.Request(
                url="https://audiences.api.drift.com/visitor/searchWithCounts",
                callback=self.parse_account_list,
                method='POST',
                body='''{
                    "sorts": [
                        {
                            "property": "session.activeSessionStartedAt",
                            "order": "DESC"
                        }
                    ],
                    "matchAll": [
                        {
                            "property": "updatedAt",
                            "value": "''' + str(startTime) + '''",
                            "operation": "GTE"
                        },
                        {
                            "property": "updatedAt",
                            "value": "''' + str(endInterval) + '''",
                            "operation": "LTE"
                        },
                        {
                            "property": "company.name",
                            "value": "Magic Leap",
                            "operation": "NEQ"
                        }  
                    ],
                    "matchAny": [],
                    "filterGroups": [],
                    "size": 9999,
                    "timezone": "America/New_York"
                }''',
                headers={
                    "content-type": "application/json",
                    "authorization": "Bearer " + self.bearerAuthToken
                })

    def parse_account_list(self, response):
        rawVisits = json.loads(response.text)
        rawVisitors = DriftRawVisitorActivity(driftRawVisitorJSON = rawVisits['visitors'])
        self.logger.info("Scraped all raw visits for this date range")
        return rawVisitors

  
