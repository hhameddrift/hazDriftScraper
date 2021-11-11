# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .items import DriftAccountList, DriftAccountUserList, DriftRawVisitorActivity, DriftUserActivity
from scrapy.utils.project import get_project_settings
import json
import os
import datetime

class DriftScrapyProjectPipeline:
    def process_item(self, item, spider):
        return item

class JsonWriterPipeline:


    settings = get_project_settings()
    outputFolder = './' + settings.get('OUTPUT_FOLDER') + '/'
    raw_output_folder = './' + settings.get('RAW_OUTPUT_FOLDER') + '/'
    accounts_filename = outputFolder + 'accounts.json'
    companies_filename = outputFolder + 'raw_companies.json'
    companies_list = []
    account_users_filename = outputFolder + 'account_users.json'
    account_users_list = []
    end_user_activity_list = []
    raw_visitor_activity_filename = raw_output_folder + 'raw_visitor_activity'
    raw_visitor_activity_list = []

    def open_spider(self, spider):
        os.makedirs(os.path.dirname(self.outputFolder), exist_ok=True)
        if spider.name == "driftSpider":
            self.end_user_activity_filename = self.outputFolder + 'end_user_activity.json'
            self.accounts = open(self.accounts_filename, 'w')
            self.account_users = open(self.account_users_filename, 'w')
            self.end_user_activity = open(self.end_user_activity_filename, 'w')
        if spider.name == "driftSpiderRaw":
            os.makedirs(os.path.dirname(self.raw_output_folder), exist_ok=True)
            fromDate = datetime.datetime.strptime(spider.custom_settings['START_DATE'], "%m/%d/%Y")
            fileWriteStartDate = str(fromDate.month) + "-" + str(fromDate.day) + "-" + str(fromDate.year)
            toDate = datetime.datetime.strptime(spider.custom_settings['END_DATE'], "%m/%d/%Y")
            fileWriteEndDate = str(toDate.month) + "-" + str(toDate.day) + "-" + str(toDate.year)
            self.raw_visitor_activity = open(self.raw_visitor_activity_filename + "_" +
                                             fileWriteStartDate + "_to_" +
                                             fileWriteEndDate +
                                             '.json', 'w')
        if spider.name == "driftSpiderRawTimelines":
            self.end_user_activity_filename = self.raw_output_folder + 'end_user_activity.json'
            self.end_user_activity = open(self.end_user_activity_filename, 'w')
        if spider.name == "driftSpiderDerivedCompanyInfo":
            self.account_users = open(self.companies_filename, 'w')


    def close_spider(self, spider):
        if spider.name == "driftSpider":
            self.accounts.close()
            json.dump(self.account_users_list, self.account_users)
            self.account_users.close()
            json.dump(self.end_user_activity_list, self.end_user_activity)
            self.end_user_activity.close()
        if spider.name == "driftSpiderRaw":
            json.dump(self.raw_visitor_activity_list, self.raw_visitor_activity)
            self.raw_visitor_activity.close()
        if spider.name == "driftSpiderRawTimelines":
            json.dump(self.end_user_activity_list, self.end_user_activity)
            self.end_user_activity.close()
        if spider.name == "driftSpiderDerivedCompanyInfo":
            json.dump(self.companies_list, self.account_users)
            self.account_users.close()

    def process_item(self, item, spider):
        if isinstance(item, DriftAccountList):
            writeOut = DriftAccountList(item)
            line = json.dumps(writeOut['driftAccountList'])
            self.accounts.write(line)
        if isinstance(item, DriftAccountUserList):
            if spider.name == "driftSpiderDerivedCompanyInfo":
                writeOut = DriftAccountUserList(item)
                self.companies_list = self.companies_list + writeOut['driftAccountUserListJSON']
            else:
                writeOut = DriftAccountUserList(item)
                self.account_users_list = self.account_users_list + writeOut['driftAccountUserListJSON']
        if isinstance(item, DriftUserActivity):
            writeOut = DriftUserActivity(item)
            self.end_user_activity_list = self.end_user_activity_list + writeOut['driftUserActivityJSON']
        if isinstance(item, DriftRawVisitorActivity):
            writeOut = DriftRawVisitorActivity(item)
            self.raw_visitor_activity_list = self.raw_visitor_activity_list + writeOut['driftRawVisitorJSON']
        return item
