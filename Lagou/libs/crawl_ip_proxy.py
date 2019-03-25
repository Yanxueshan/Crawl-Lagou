__author__ = 'Yan'
__date__ = '2019/3/25 20:58'

import requests
from scrapy.selector import Selector
import pymysql

class Fetch_Proxy(object):
    '''
        从西刺网站获取免费ip代理
    '''
    def __init__(self):
        self.connect = pymysql.connect(host='localhost', db='lagou',
                                       user='root', password='lingtian..1021', charset='utf8')
        self.cursor = self.connect.cursor()

    def get_ip_list(self, url):
        '''
            获取ip_list列表
        '''
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
        }
        res = requests.get(url, headers=headers)
        selector = Selector(text=res.text)
        results = selector.css('#ip_list tr')
        for result in results[1:]:
            ip = result.css('td::text')[0].extract()
            port = result.css('td::text')[1].extract()
            self.insert_ip(ip, port)

    def judge(self, ip, port):
        '''
            判断ip是否可以用
        '''
        proxy = {'http': ip+':'+port}
        try:
            res = requests.get('https://www.baidu.com', proxies=proxy)
        except Exception:
            print('该ip：' + ip + '无效')
            return False
        else:
            if 200 <= res.status_code < 300:
                return True
            else:
                print('该ip：' + ip + '无效')
                self.delete_ip(ip, port)
                return False

    def insert_ip(self, ip, port):
        '''
            往数据库中添加数据
        '''
        insert_sql = 'insert into ip(ip, port) values("{0}", "{1}")'.format(ip, port)
        self.cursor.execute(insert_sql)
        self.connect.commit()

    def delete_ip(self, ip, port):
        '''
            从数据库中删除无效ip
        '''
        delete_sql = 'delete from ip where ip="{0}"'.format(ip)
        self.cursor.execute(delete_sql)
        self.connect.commit()

    def get_random_ip(self):
        '''
            从数据库中随机获取一个ip和port
        '''
        select_sql = 'select ip, port from ip order by rand() limit 1'
        self.cursor.execute(select_sql)
        for item in self.cursor.fetchall():
            ip, port = item
            result = self.judge(ip, port)
            if result:
                return "http://{0}:{1}".format(ip, port)
            else:
                self.get_random_ip()


if __name__ == "__main__":
    fetch = Fetch_Proxy()
    fetch.get_ip_list('https://www.xicidaili.com/wt/')
    print(fetch.get_random_ip())
