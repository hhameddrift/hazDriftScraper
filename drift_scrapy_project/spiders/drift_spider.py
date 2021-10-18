import scrapy
import json
from os import makedirs
from os.path import exists, dirname
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class DriftSpider(scrapy.Spider):
    name = 'driftSpider'
    allowed_domains = ['drift.com']
    _cookies = ''
    bearerAuthToken = ''
    outputFolder = './json_output/'
    # Date ranges to scrape with API calls
    fromTime = '1626246000000'
    toTime = '1634281199999'
    # Create output folder if it doesn't already exist.
    makedirs(dirname(outputFolder), exist_ok=True)

    # You'll need to get the filter key for "All accounts" on your drift account and replace the URL below
    # TODO: Waiting for the page title is probably not the best way to identify the page to start scraping
    #       Probably better to just start at the login page and then auto-redirect to this page so user
    #       doesn't have to click around.
    def start_requests(self):
        yield SeleniumRequest(
            url='https://app.drift.com/conversations/prospector/accounts?filters=eyJ2ZXJzaW9uIjoyLCJmaWx0ZXJHcm91cHNCeVBhZ2UiOnsiQUNDT1VOVFMiOltdLCJBQ0NPVU5UX0RFVEFJTFMiOltdLCJDT05UQUNUX0RFVEFJTFMiOltdLCJBQ1RJVklUSUVTIjpbW11dfX0&savedFilterId=0',
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
                "sortBy":"ENGAGEMENT_SCORE",
                "descending":"true",
                "accountName":"",
                "fromTime":'''+ self.fromTime + ''',
                "toTime":''' + self.toTime + ''',
                "filterGroups":[]
            }''',
            headers={
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "authorization": "Bearer " + self.bearerAuthToken
            })

    def parse_account_list(self, response):
        accounts_file = open(self.outputFolder + 'accounts.json', 'w')
        n = accounts_file.write(response.text)
        accounts_file.close()
        accounts_json = json.loads(response.text)
        for account in accounts_json['data']:           
            #print(response.body)
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
                    "accept": "application/json, text/plain, */*",
                    "content-type": "application/json",
                    "authorization": "Bearer " + self.bearerAuthToken
                },
                cb_kwargs=dict(accountID=account["accountId"])
            )
        # For each account, get the accountID and iterate the loop
        # for account in accounts_json:



    def parse_account_contacts(self, response, accountID):
        contacts_file = open(self.outputFolder + 'account_'+accountID+'_contacts.json', 'w')
        n = contacts_file.write(response.text)
        contacts_file.close()
        contacts_json = json.loads(response.text)
        print(contacts_json)
        for contact in contacts_json:
        # Request GET - same headers as POST
        # https://customer.api.drift.com/end_users/xxxxxxxxxxx
            yield scrapy.Request(url="https://customer.api.drift.com/end_users/"+str(contact["endUserId"]),
                callback=self.parse_end_user,
                method='GET',
                headers={
                    "accept": "application/json, text/plain, */*",
                    "content-type": "application/json",
                    "authorization": "Bearer " + self.bearerAuthToken
                }
            )

    def parse_end_user(self, response):
        end_user_response_json = json.loads(response.text)
        end_user_output_file = self.outputFolder + "end_users.json"
        if not exists(end_user_output_file):
            new_end_user_file = open(end_user_output_file, 'w')
            json.dump([end_user_response_json], new_end_user_file, indent = 4)
            new_end_user_file.close()
        else:
            with open(end_user_output_file,'r+') as file:
                # First we load existing data into a dict.
                file_data = json.load(file)
                # Join new_data with file_data inside emp_details
                file_data.append(end_user_response_json)
                # Sets file's current position at offset.
                file.seek(0)
                # convert back to json.
                json.dump(file_data, file, indent = 4)

  