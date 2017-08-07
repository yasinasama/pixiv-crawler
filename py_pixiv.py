import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime


CRAWL_Url = 'https://www.pixiv.net/ranking.php?mode=monthly'  # 需要抓取的URL
DOWNLOAD_PATH = 'D:\pixiv'   # 图片存放地址


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


def downloadPath(path):
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def getRequest(req, url, headers, stream=False):
    return req.get(url=url, headers=headers, stream=stream) if req else requests.get(url=url, headers=headers, stream=stream)


def loginPixiv():
    # 获取session实例
    p = requests.Session()
    # 获取post请求必要数据
    p.headers = headers
    r = getRequest(req=p, url='https://accounts.pixiv.net/login', headers=headers)
    parrern = re.compile(r'name="post_key" value="(.*?)">')
    res = parrern.search(r.text)
    data['post_key'] = res.group()

    # post请求模拟登陆
    print('模拟登陆开始......')
    try:
        p.post(url='https://accounts.pixiv.net/api/login', data=data)
        print('模拟登陆成功......')
        return p
    except:
        print('模拟登陆失败......')
        raise

login = loginPixiv()
result = getRequest(req=login, url=CRAWL_Url, headers=headers)

# 获取我们分析的主要的DOM节点信息
soup = BeautifulSoup(result.text, "html.parser")
items = soup.find_all(class_='ranking-item')
items_length = len(items)

re_filename = re.compile('(\d+)')
downloadpath = downloadPath(DOWNLOAD_PATH)

for i in range(10):
    image_url = 'https://www.pixiv.net' + items[i].find(class_='ranking-image-item').a.get('href')
    headers['Referer'] = image_url
    filename = re.search(re_filename, image_url).group() + '.jpg'
    fullpath = os.path.join(downloadpath, filename)

    page_count = items[i].find(class_='page-count')
    if page_count:

    else:
        small_jpg_url = items[i].find('img').get('data-src')

        large_jpg_url = small_jpg_url.replace(r'c/240x480/img-master', 'img-original').replace('_master1200', '')
        print(large_jpg_url)
        large_png_url = large_jpg_url.replace('jpg', 'png')

        jpg = getRequest(req=login, url=large_jpg_url, headers=headers, stream=True)
        png = getRequest(req=login, url=large_png_url, headers=headers, stream=True)
    with open(fullpath, 'wb') as f:
        if jpg.status_code == 200:
            print('抓取开始%s' % filename)
            s = datetime.now()
            f.write(jpg.content)
            print('抓取完毕 , 耗时 %s 秒 , 文件大小 %s KB' % ((datetime.now()-s).seconds, int(os.path.getsize(fullpath)/1024)))
        elif png.status_code == 200:
            print('抓取开始%s' % filename)
            s = datetime.now()
            f.write(png.content)
            print('抓取完毕 , 耗时 %s 秒 , 文件大小 %s KB' % ((datetime.now() - s).seconds, int(os.path.getsize(fullpath)/1024)))
        else:
            print('NOT FOUND')





