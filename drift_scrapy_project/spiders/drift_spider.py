import scrapy
import json
import time
import datetime
from os import makedirs
from os.path import exists, dirname
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from drift_scrapy_project.items import DriftAccountList, DriftAccountUserList, DriftUserActivity

class DriftSpider(scrapy.Spider):
    name = 'driftSpider'
    allowed_domains = ['drift.com']
    _cookies = ''
    bearerAuthToken = ''
    userCount = 0
    companyCount = 0

    custom_settings = {
        'START_DATE': '10/1/2021',
        'END_DATE': '10/1/2021'
    }

    def __init__(self, startDate="", endDate="", *args, **kwargs):
        super(DriftSpider, self).__init__(*args, **kwargs)
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
            url='https://app.drift.com/conversations/prospector/activity',
            #url="https://drift.com",
            wait_time=120,
            wait_until=EC.title_is('Drift | Account Activity'),
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
        yield scrapy.Request(
            url="https://account-activity.drift.com/v2/accounts/search_with_activities/?pageSize=500",
            callback=self.parse_account_list,
            method='POST',
            body='''{
                "sortBy":"ACCOUNT_NAME",
                "descending":"false",
                "accountName":"",
                "fromTime":'''+ str(self.fromTimeStamp) + ''',
                "toTime":''' + str(self.toTimeStamp) + ''',
                "filterGroups":[]
            }''',
            headers={
                "content-type": "application/json",
                "authorization": "Bearer " + self.bearerAuthToken
            })

    def parse_account_list(self, response):
        accounts = json.loads(response.text)
        accountItem = DriftAccountList(driftAccountList = accounts)
        self.logger.info("Scraped all accounts")
        yield accountItem
        for account in accounts['data']:           
            # Use this to not pull Magic Leap account (employee) activity
            # if (account["accountId"] != "5002912_magicleap.com"):

            # Request POST - same headers as POST above
            # https://account-activity.drift.com/v2/accounts/xxxxxxx_xxxxxxxxxxxx/contacts
            yield scrapy.Request(
                url="https://account-activity.drift.com/v2/accounts/"+account["accountId"]+"/contacts",
                callback=self.parse_account_contacts,
                method='POST',
                body='''{
                    "sortBy":"CONTACT_NAME",
                    "activityTypes":["PAGE_VIEW","CONVERSATION","MEETING_BOOKED","MEETING_CANCELED","VIDEO","EMAIL_OPEN","EMAIL_CLICK","END_USER_IDENTIFIED"],
                    "descending":true,
                    "contactFilterType":"ALL"
                    }''',
                headers={
                    "content-type": "application/json",
                    "authorization": "Bearer " + self.bearerAuthToken
                },
                cb_kwargs=dict(accountID=account["accountId"])
            )

    def parse_account_contacts(self, response, accountID):
        account_users_response_json = json.loads(response.text)
        account_user_item = DriftAccountUserList(driftAccountUserListJSON = account_users_response_json)
        self.companyCount = self.companyCount + 1
        self.logger.info("Scraped Company " + accountID + " - #" + str(self.companyCount))
        yield account_user_item

        for contact in account_users_response_json:
        # Request GET - same headers as POST
        # https://customer.api.drift.com/end_users/xxxxxxxxxxx
            yield scrapy.Request(url="https://customer.api.drift.com/end_users/"+str(contact["endUserId"])+"/timeline?size=999&offset=0&resolveMaster=false&filter=EVENT",
                callback=self.parse_end_user,
                method='GET',
                headers={
                    "authorization": "Bearer " + self.bearerAuthToken
                },
                cb_kwargs=dict(accountID=accountID, endUserID=str(contact["endUserId"]))
            )
        

    def parse_end_user(self, response, accountID, endUserID):
        end_user_response_json = json.loads(response.text)
        end_user_item = DriftUserActivity(driftUserActivityJSON = end_user_response_json)
        self.userCount = self.userCount + 1
        reportOut = "Scraped EndUser " + endUserID + " from Company " + accountID + " - #" + str(self.userCount)
        self.logger.info(reportOut)
        print(reportOut)
        return end_user_item

  
