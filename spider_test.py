__author__ = 'Yan'
__date__ = '2019/3/25 19:35'

from scrapy.selector import Selector
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
}


def get(url):
    resp = requests.get(url, headers=headers)
    selector = Selector(text=resp.text)
    position = selector.css('.job-name::attr(title)').extract_first('')
    job_tags = selector.css('dd.job_request span')
    salary = job_tags[0].css('::text').extract_first('')
    work_city = job_tags[1].css('::text').extract_first('')
    experience = job_tags[2].css('::text').extract_first('')
    education = job_tags[3].css('::text').extract_first('')
    work_category = job_tags[4].css('::text').extract_first('')
    desc = selector.css('.job-detail p')
    result = []
    for des in desc:
        data = des.css('::text').extract_first('')
        result.append(data)
    work_addrs = selector.css('.work_addr a')
    resu = []

    work_add_desc = selector.css('.work_addr')
    for i in work_add_desc:
        data = i.css("::text")
        resu.append(data)
    res = []

    for work_addr in work_addrs:
        data = work_addr.css('::text').extract_first('')
        res.append(data)
    company_name = selector.css('.job_company_content em::text').extract_first('')
    company_url = selector.css('#job_company dt a::attr(href)').extract_first('')
    publish_time = selector.css('.publish_time::text').extract_first('')
    pass

if __name__ == "__main__":
    url = 'https://www.lagou.com/jobs/5742311.html'
    get(url)
