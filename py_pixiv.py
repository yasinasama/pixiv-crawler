import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

MAX_RANK_PAGE = 10
CRAWL_Url = 'https://www.pixiv.net/ranking.php?mode=daily&p=1'  # 需要抓取的URL
DOWNLOAD_PATH = 'D:\pixiv'  # 图片存放地址

re_filename = re.compile('(\d+)')

MODE_LIST = {
    '1': 'daily',
    '2': 'weekly',
    '3': 'monthly',
    '4': 'rookie',
    '5': 'original',
    '6': 'male',
    '7': 'female'
}

# 防盗链
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36',
    'Referer': ''
}

param = {
    'mode': '',
    'date': ''
}
# post请求内容
data = {
    'pixiv_id': '',
    'password': '',
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


def isImageExist(filename):
    return True if os.path.exists(filename) else False


def loginPixiv():
    pixiv_id = input('请输入账号: ')
    password = input('请输入密码: ')
    # 获取session实例
    p = requests.Session()
    # 获取post请求必要数据
    p.headers = headers
    r = p.get(url='https://accounts.pixiv.net/login', headers=headers)
    parrern = re.compile(r'name="post_key" value="(.*?)">')
    res = parrern.search(r.text)
    data['post_key'] = res.group()
    data['pixiv_id'] = pixiv_id
    data['password'] = password

    # post请求模拟登陆
    print('模拟登陆开始......')
    try:
        p.post(url='https://accounts.pixiv.net/api/login', data=data)
        print('模拟登陆成功......')
        return p
    except:
        print('模拟登陆失败......')
        raise


def getCrawlUrl():
    mode_input = input('请选择你感兴趣的(输入对应数字即可): 1 今日,2 本周,3 本月,4 新人,5 原创,6 受男性欢迎,7 受女性欢迎 ------------- ')
    date = input('请输入日期:  例如20170808 -----------  ')
    mode = MODE_LIST[mode_input]
    url_list = []
    for i in range(MAX_RANK_PAGE):
        url_list.append('https://www.pixiv.net/ranking.php?mode=%s&date=%s&p=%s' % (mode, date, i + 1))
    return url_list


def isSingleImage(imgdom):
    return False if imgdom.find(class_='page-count') else True


# 单张图片抓取
def singleImageCrawl(small_jpg_url, filename, login_req):
    downloadpath = downloadPath(DOWNLOAD_PATH)
    large_jpg_url = small_jpg_url.replace(r'c/240x480/img-master', 'img-original').replace('_master1200', '')
    large_png_url = large_jpg_url.replace('jpg', 'png')
    print(large_jpg_url)
    downloadImage(downloadpath, filename, large_jpg_url, large_png_url, login_req)


# 多张图片抓取
def manyImageCrawl(small_jpg_url, filename, imgdom, login_req):
    downloadpath = downloadPath(DOWNLOAD_PATH)
    page_count = imgdom.find(class_='page-count').span.text
    for j in range(int(page_count)):
        f = filename.replace('.', '-' + str(j) + '.')
        p = '_p' + str(j) + '_'
        large_jpg_url = small_jpg_url.replace(r'c/240x480/', '').replace('_p0_', p)
        print(large_jpg_url)
        large_png_url = large_jpg_url.replace('jpg', 'png')
        downloadImage(downloadpath, f, large_jpg_url, large_png_url, login_req)


# 图片下载
def downloadImage(downloadpath, filename, jpgurl, pngurl, login_req):
    fullpath = os.path.join(downloadpath, filename)
    jpg = login_req.get(url=jpgurl, headers=headers, stream=True)
    png = login_req.get(url=pngurl, headers=headers, stream=True)
    if not isImageExist(fullpath):
        with open(fullpath, 'wb') as f:
            if jpg.status_code == 200:
                print('图片下载开始%s' % filename)
                s = datetime.now()
                f.write(jpg.content)
                print('图片下载结束 , 耗时 %s 秒 , 文件大小 %s KB' % ((datetime.now() - s).seconds, int(os.path.getsize(fullpath) / 1024)))
            elif png.status_code == 200:
                print('图片下载开始%s' % filename)
                s = datetime.now()
                f.write(png.content)
                print('图片下载结束 , 耗时 %s 秒 , 文件大小 %s KB' % ((datetime.now() - s).seconds, int(os.path.getsize(fullpath) / 1024)))
            else:
                print('图片下载出错!!!')
    else:
        print('图片已存在!!')


# 登录
login = loginPixiv()
list = getCrawlUrl()
for url in list:
    result = login.get(url=url, headers=headers)
    # 获取我们分析的主要的DOM节点信息
    soup = BeautifulSoup(result.text, "html.parser")
    items = soup.find_all(class_='ranking-item')
    items_length = len(items)
    for i in range(1):
        curr_dom = items[i]
        image_url = 'https://www.pixiv.net' + curr_dom.find(class_='ranking-image-item').a.get('href')
        small_jpg_url = curr_dom.find('img').get('data-src')
        headers['Referer'] = image_url
        filename = re.search(re_filename, image_url).group() + '.jpg'

        if isSingleImage(curr_dom):
            singleImageCrawl(small_jpg_url, filename, login)
        else:
            manyImageCrawl(small_jpg_url, filename, curr_dom, login)
