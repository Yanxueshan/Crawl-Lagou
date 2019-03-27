# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import pickle

from scrapy import signals
from fake_useragent import UserAgent
from libs.crawl_ip_proxy import Fetch_Proxy
from scrapy.http import HtmlResponse
from settings import BASE_DIR
from selenium.webdriver.common.keys import Keys
from chaojiying import Chaojiying_Client
from scrapy.selector import Selector
import re
import time
import requests


class LagouSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class LagouDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomUserAgentDownloaderMiddleware(object):
    '''
        为每次请求添加随机User-Agent
    '''
    def __init__(self, crawler):
        super().__init__()
        self.user_agent = UserAgent()

    @classmethod
    def from_crawler(cls, crawler):
        '''
            自己写Middleware必须实现的函数，manager会自主调用
        '''
        return cls(crawler)

    def process_request(self, request, spider):
        '''
            具体的随机添加User-Agent处理逻辑
        '''
        request.headers.setdefault("User-Agent", self.user_agent.random)


class ProxyIPDownloaderMiddleware(object):
    '''
        设置IP代理防止反爬
    '''
    def __init__(self, crawler):
        self.fetch = Fetch_Proxy()
        super().__init__()

    @classmethod
    def from_crawler(cls, crawler):
        '''
            自己写Middleware必须实现的函数，manager会自主调用
        '''
        return cls(crawler)

    def process_request(self, request, spider):
        '''
            具体的设置IP代码的处理逻辑
        '''
        request.meta["proxy"] = self.fetch.get_random_ip()


class RedirectDownloaderMiddleware(object):
    '''
        当拉勾网发现账号异常从而连接到认证页面时，需要识别验证码，通过该middleware进行拦截，对302进行处理
    '''
    def process_response(self, request, response, spider):
        '''
            对拉勾网重定向302的解决，捕捉到302URL，然后进行处理
        '''
        re_match = re.match('.*?/utrack/verify.*', response.url)
        if re_match:
            url = re_match.group(0)
            # 向302URL发起请求，识别验证码，并继续访问
            spider.browser.get(url)
            while True:
                selector = Selector(text=spider.browser.page_source)
                captcha_url = selector.css('#captcha::attr(src)').extract_first('')
                if not captcha_url:
                    break
                captcha_url = "https://www.lagou.com" + captcha_url
                image = requests.get(captcha_url)

                chaojiying = Chaojiying_Client('Yanxueshan', 'lingtian..1021', '898966')
                result = chaojiying.PostPic(image.content, 1005)['pic_str']

                spider.browser.find_element_by_css_selector("#code").send_keys(result)
                spider.browser.find_element_by_css_selector("#submit").click()

                return HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source,
                            encoding="utf-8", request=request)
        return response
