# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from datetime import datetime, timedelta
from items import LagouItem
from libs.common import get_md5
import re


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['http://www.lagou.com/']

    rules = (
        Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        item = {}
        #item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
        #item['name'] = response.xpath('//div[@id="name"]').get()
        #item['description'] = response.xpath('//div[@id="description"]').get()
        return item

    def parse(self, response):
        lagou_item = LagouItem()

        position = response.css('.job-name::attr(title)').extract_first('')

        job_tags = response.css('dd.job_request span')

        salary = job_tags[0].css('::text').extract_first('')
        min_salary, max_salary = self.handle_salary(salary)

        work_city = job_tags[1].css('::text').extract_first('')

        experience = job_tags[2].css('::text').extract_first('')
        min_experience, max_experience = self.handle_experience(experience)

        education = job_tags[3].css('::text').extract_first('')
        work_category = job_tags[4].css('::text').extract_first('')

        job_desc = response.css('.job-detail p')
        position_desc = []
        for desc in job_desc:
            data = desc.css('::text').extract_first('')
            if data:
                position_desc.append(data)
        position_desc = '\n'.join(position_desc)

        workplace_tags = response.css('.work_addr')
        workplace = []
        for workplace_tag in workplace_tags:
            data = workplace_tag.css("::text").extract_first('')
            workplace.append(data)
        workplace = '-'.join(workplace[:-1])

        company_name = response.css('.job_company_content em::text').extract_first('')
        company_url = response.css('#job_company dt a::attr(href)').extract_first('')

        publish_date = response.css('.publish_time::text').extract_first('')
        publish_date = self.handle_publish_date(publish_date)

        lagou_item["url"] = response.url
        lagou_item["url_object_id"] = get_md5(response.url)
        lagou_item["position"] = position
        lagou_item["min_salary"] = min_salary
        lagou_item["max_salary"] = max_salary
        lagou_item["work_city"] = work_city
        lagou_item["min_experience"] = min_experience
        lagou_item["max_experience"] = max_experience
        lagou_item["education"] = education
        lagou_item["work_category"] =work_category
        lagou_item["position_desc"] = position_desc
        lagou_item["workplace"] = workplace
        lagou_item["company_name"] = company_name
        lagou_item["company_url"] = company_url
        lagou_item["publish_date"] = publish_date

        yield lagou_item

    def handle_salary(self, salary):
        '''
        对salary字符串进行处理，提取出其中的min_salary和max_salary
        :param salary: 薪资
        :return: min_salary, max_salary
        '''
        re_match = re.match('(\d+k).*?(\d+k).*', salary)
        if re_match:
            min_salary = re_match.group(1)
            max_salary = re_match.group(2)
        else:
            min_salary = 0
            max_salary = 0
        return min_salary, max_salary

    def handle_experience(self, experience):
        '''
        对experience字符串进行处理，提取出其中的min_experience和max_experience
        :param experience:
        :return: min_experience, max_experience
        '''
        re_match = re.match('(\d+k).*?(\d+k).*', experience)
        min_experience = 0
        max_experience = 0
        if re_match:
            if re_match.group(1) and re_match.group(2):
                min_experience = re_match.group(1)
                max_experience = re_match.group(2)
            elif re_match.group(1) and not re_match.group(2) and '以下' in experience:
                min_experience = 0
                max_experience = re_match.group(1)
            elif re_match.group(1) and not re_match.group(2) and '以上' in experience:
                min_experience = re_match.group(1)
                max_experience = 100
        return min_experience, max_experience

    def handle_publish_date(self, publish_date):
        '''
        对publish_date进行处理
        :param publish_date:
        :return: publih_date
        '''
        publish_date = publish_date.replace('发布于拉勾网', '').strip()
        if '天前' in publish_date:
            re_match = re.match('(\d+).*?', publish_date)
            publish_date = datetime.now() - timedelta(days=int(re_match.group(1)))
        else:
            publish_date = datetime.now()
        return publish_date
