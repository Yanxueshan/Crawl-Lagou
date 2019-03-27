# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from datetime import datetime, timedelta
from items import LagouItem
from libs.common import get_md5
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from settings import BASE_DIR
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
import re
import os
import time
import pickle


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']

    rules = (
        Rule(LinkExtractor(allow=r'zhaopin/.*'), follow=True),
        Rule(LinkExtractor(allow=(r'gongsi/j\d+.html', )), follow=True),
        Rule(LinkExtractor(allow=r'jobs/\d+.html'), callback='parse_job', follow=True),
    )

    # scrapy默认处理 >=200 并且 <300的URL，其他的会过滤掉，handle_httpstatus_list表示对返回这些状态码的URL不过滤，自己处理
    handle_httpstatus_list = [302, 403, 404]

    def __init__(self):
        # scrapy集成selenium
        chrome_opt = Options()
        chrome_opt.add_argument("--disable-extensions")
        chrome_opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.browser = webdriver.Chrome(executable_path="C:/Users/晏乐/Desktop/Lagou/chromedriver", chrome_options=chrome_opt)

        # crawl_url_count: 用来统计爬取URL的总数
        self.crawl_url_count = 0

        # 信号处理，当爬虫退出时执行spider_closed方法
        dispatcher.connect(self.spider_closed, signals.spider_closed)

        # 信号处理，当引擎从downloader中获取到一个新的Response对象时调用get_crawl_url_count方法
        dispatcher.connect(self.get_crawl_url_count, signals.response_received)

        # 数据收集，收集Scrapy运行过程中302/403/404页面URL及URL数量
        # failed_url: 用来存放302/403/404页面URL
        self.failed_url = []

        super().__init__()

    def spider_closed(self, spider):
        '''
            当爬虫退出时关闭chrome，收集爬取失败（302/403/404）的URL，并写入json文件中
        '''
        self.browser.quit()
        self.crawler.stats.set_value("failed_urls", ','.join(self.failed_url))
        pickle.dump(self.failed_url, open(BASE_DIR+"/failed_url/failed_url.json", 'wb'))

    def get_crawl_url_count(self, spider):
        '''
            当引擎engine从downloader中获取到一个新的Response对象时调用，crawl_url_count+=1
        '''
        self.crawl_url_count += 1
        print("截止目前，爬取URL总数为：", self.crawl_url_count)
        return self.crawl_url_count

    def start_requests(self):
        # chromedriver中有一些js变量会暴露，被服务器识别出来，所以需要手动启动chromedriver
        # 1. 找到chrome.exe文件所在路径，cmd中进入该路径，执行chrome.exe --remote-debugging-port=9222
        # 2. 执行下列语句（执行第一步时要保证127.0.0.1:9222/json能够正常访问，在这之前需要退出所有的chrome）
        # 需要注意的是cookies是有过期时间的，如果过期了如何解决？
        # 当拉勾网发现账号异常从而cookies失效时，或者cookies过期了，从而链接到登录页面时，需要通过middleware进行拦截，从而再次进行模拟登录
        # 实现思路：书写一个downloadermiddleware，重写process_response，如果response.url（重定向url）为登录页面url，则再次通过selenium进行模拟登录
        cookies = []
        if os.path.exists(BASE_DIR+"/cookies/lagou.cookies"):
            cookies = pickle.load(open(BASE_DIR+"/cookies/lagou.cookies", "rb"))
        if not cookies:
            self.browser.get("https://passport.lagou.com/login/login.html")
            self.browser.find_element_by_css_selector('.form_body .input.input_white').send_keys(Keys.CONTROL+"a")
            self.browser.find_element_by_css_selector('.form_body .input.input_white').send_keys('13725541420')
            self.browser.find_element_by_css_selector('.form_body input[type="password"]').send_keys(Keys.CONTROL+"a")
            self.browser.find_element_by_css_selector('.form_body input[type="password"]').send_keys('lingtian..1021')
            self.browser.find_element_by_css_selector('div[data-view="passwordLogin"] input.btn_lg').click()
            time.sleep(20)
            cookies = self.browser.get_cookies()
            pickle.dump(cookies, open(BASE_DIR+"/cookies/lagou.cookies", "wb"))

        cookies_dict = {}
        for cookie in cookies:
            cookies_dict[cookie["name"]] = cookie["value"]

        for url in self.start_urls:
            yield scrapy.Request(url, dont_filter=True, cookies=cookies_dict)

    def parse_job(self, response):
        '''
            从response中解析出想要的数据
        '''
        if response.status in [302, 403, 404]:
            self.failed_url.append(response.url)
            # 数据收集，当Response状态码为302/403/404时，failed_url数加1
            self.crawler.stats.inc_value("failed_url")

        lagou_item = LagouItem()

        # position: 职位名称
        position = response.css('.job-name::attr(title)').extract_first('')
        job_tags = response.css('dd.job_request span')

        # min_salary: 最低薪资   max_salary: 最高薪资
        salary = job_tags[0].css('::text').extract_first('')
        min_salary, max_salary = self.handle_salary(salary)

        # work_city: 工作城市
        work_city = job_tags[1].css('::text').extract_first('').replace('/', '').strip()

        # min_experience: 最低工作年限   max_experience: 最高工作年限
        experience = job_tags[2].css('::text').extract_first('')
        min_experience, max_experience = self.handle_experience(experience)

        # education: 最低学历要求
        education = job_tags[3].css('::text').extract_first('').replace('/', '').strip()
        education = self.handle_education(education)
        # work_category: 工作性质（全职/兼职/实习）
        work_category = job_tags[4].css('::text').extract_first('')

        # position_desc: 职位描述
        job_desc = response.css('.job-detail p')
        position_desc = []
        for desc in job_desc:
            data = desc.css('::text').extract_first('')
            if data:
                position_desc.append(data)
        position_desc = '\n'.join(position_desc)

        # workplace: 工作地点
        workplace_tags = response.css('.work_addr a')
        workplace = []
        for workplace_tag in workplace_tags:
            data = workplace_tag.css("::text").extract_first('')
            workplace.append(data)
        workplace = '-'.join(workplace[:-1])

        # company_name: 招聘公司名称   company_url: 招聘公司链接
        company_name = response.css('.job_company_content em::text').extract_first('').replace('/', '').strip()
        company_url = response.css('#job_company dt a::attr(href)').extract_first('')

        # publish_date: 职位发布时间
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
        lagou_item["work_category"] = work_category
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
        re_match = re.match('(\d+)k.*?(\d+)k.*', salary)
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
        re_match = re.match('.*?(\d+).*?(\d+).*', experience)
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
            publish_date = datetime.now().date() - timedelta(days=int(re_match.group(1)))
        else:
            publish_date = datetime.now().date()
        return publish_date

    def handle_education(self, education):
        '''
            对education进行处理，提取出最低学历要求
            :param education:
            :return: education
        '''
        if '学历不限' in education:
            education = '不限'
        else:
            education = education.replace('及以上', '')
        return education
