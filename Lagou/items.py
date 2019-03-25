# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class LagouItem(scrapy.Item):
    '''
        设置需要保存的数据字段
    '''
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    position = scrapy.Field()  # 职位名称
    min_salary = scrapy.Field()  # 最低薪资
    max_salary = scrapy.Field()  # 最高薪资
    work_city = scrapy.Field()  # 工作城市
    min_experience = scrapy.Field()  # 最低经验要求
    max_experience = scrapy.Field()  # 最高经验要求
    education = scrapy.Field()  # 学历要求
    work_category = scrapy.Field()  # 工作性质（全职/兼职/实习）
    position_desc = scrapy.Field()  # 职位描述
    workplace = scrapy.Field()  # 工作地点
    company_name = scrapy.Field()  # 公司名称
    comany_url = scrapy.Field()  # 公司url地址
    publish_date = scrapy.Field()  # 职位发布时间
