import requests
from bs4 import BeautifulSoup
import re
import os


def getRequest(req, url, headers, stream=False):
    return req.get(url=url, headers=headers, stream=stream) if req else requests.get(url=url, headers=headers, stream=stream)


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36',
    'Referer': ''
}

data = {
    'pixiv_id': '614867000@qq.com',
    'password': 'yasina',
    'captcha': '',
    'g_recaptcha_response': '',
    'source': 'pc',
    'ref': 'wwwtop_accounts_index',
    'return_to': 'https://www.pixiv.net/',
    'post_key': ''
}

# 需要抓取的URL
Crawl_Url = 'https://www.pixiv.net/ranking.php?mode=monthly'

# 获取session实例
p = requests.Session()

# 获取post请求必要数据
p.headers = headers
r = getRequest(req=p, url='https://accounts.pixiv.net/login', headers=headers)
parrern = re.compile(r'name="post_key" value="(.*?)">')
res = parrern.search(r.text)
data['post_key'] = res.group()

# post请求模拟登陆
t = p.post(url='https://accounts.pixiv.net/api/login', data=data)
result = getRequest(req=p, url=Crawl_Url, headers=headers)

# 获取我们分析的主要的DOM节点信息
soup = BeautifulSoup(result.text, "html.parser")
items = soup.find_all(class_='ranking-item')
items_length = len(items)

re_download_name = re.compile('(\d+)')

for i in range(5):
    image_url = 'https://www.pixiv.net' + items[i].find(class_='ranking-image-item').a.get('href')

    small_jpg_url = items[i].find('img').get('data-src')

    large_jpg_url = small_jpg_url.replace(r'c/240x480/img-master', 'img-original').replace('_master1200', '')
    large_png_url = large_jpg_url.replace('jpg', 'png')

    download_name = re.search(re_download_name, image_url).group()+'.jpg'

    headers['Referer'] = image_url

    jpg = getRequest(req=p, url=large_jpg_url, headers=headers, stream=True)
    png = getRequest(req=p, url=large_png_url, headers=headers, stream=True)
    with open(download_name, 'wb') as f:
        if jpg.status_code == 200:
            print('get it JPG!')
            f.write(jpg.content)
        elif png.status_code == 200:
            print('get it PNG!')
            f.write(png.content)
        else:
            print('NOT FOUND')





