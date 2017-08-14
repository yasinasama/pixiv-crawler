import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
import gif_downloader

MAX_RANK_PAGE = 1  # 50 * MAX_RANK_PAGE   MAX 10
MAX_EACH_PAGE = 50  # MAX_EACH_PAGE/50     MAX 50
MAX_MANY_IMAGE_COUNT = 5  # 多图中抓取数
DOWNLOAD_PATH = 'D:\pixiv\image'  # 图片存放地址
GIF_DOWNLOAD_PATH = 'D:\pixiv\gif'  # 动图存放地址

THREAD_COUNT = 20

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

CONTENT_LIST = {
    '1': '',  # 综合
    '2': 'illust',  # 插画
    '3': 'ugoira',  # 动图
}
# Referer防盗链
# Range断点获取响应内容
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36',
    'Referer': '',
    'Range': ''
}

param = {
    'mode': '',
    'date': '',
    'content': ''
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


# 文件保存路径
def getdownloadPath(path):
    if not os.path.exists(path):
        os.mkdir(path)
    return path


# 图片存在？
def isImageExist(filename):
    return True if os.path.exists(filename) else False


# 单张图片？
def isSingleImage(imgdom):
    return False if imgdom.find(class_='page-count') else True


# 图片 OR GIF
def getImageType(url):
    if url.find('_p0') > 0:
        return 'image'
    else:
        return 'gif'


# 登录
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
    while True:
        content_input = input('请选择你感兴趣的内容(输入对应数字即可): 1 综合,2 插画,3 动图 >>>>>')
        if content_input == '1':
            mode_input = input('请选择你感兴趣的排序方式(输入对应数字即可): 1 今日,2 本周,3 本月,4 新人,5 原创,6 受男性欢迎,7 受女性欢迎 >>>>>>')
        elif content_input == '2':
            mode_input = input('请选择你感兴趣的(输入对应数字即可): 1 今日,2 本周,3 本月,4 新人 >>>>>>')
        elif content_input == '3':
            mode_input = input('请选择你感兴趣的(输入对应数字即可): 1 今日,2 本周 >>>>>>')
        else:
            print('请正确输入!!!')
            continue
        date = input('请输入日期:  例如20170101 -----------  ')
        today = datetime.strftime(datetime.date(datetime.now()), '%Y%m%d')

        if date < today:
            content = CONTENT_LIST[content_input]
            mode = MODE_LIST[mode_input]
            url_list = []
            for i in range(MAX_RANK_PAGE):
                if content == '':
                    url_list.append('https://www.pixiv.net/ranking.php?mode=%s&date=%s&p=%s' % (mode, date, i + 1))
                else:
                    url_list.append('https://www.pixiv.net/ranking.php?mode=%s&content=%s&date=%s&p=%s' % (mode, content, date, i + 1))
            return url_list
        else:
            print('输入日期必须早于当前日期!!!!')


# 单张图片抓取
def singleImageCrawl(small_jpg_url, filename, login_req,image_url):
    downloadpath = getdownloadPath(DOWNLOAD_PATH)
    large_jpg_url = small_jpg_url.replace(r'c/240x480/img-master', 'img-original').replace('_master1200', '')
    large_png_url = large_jpg_url.replace('jpg', 'png')
    downloadImage(downloadpath, filename, large_jpg_url, large_png_url, login_req,image_url)


# 多张图片抓取
def manyImageCrawl(small_jpg_url, filename, imgdom, login_req,image_url):
    downloadpath = getdownloadPath(DOWNLOAD_PATH)
    page_count = imgdom.find(class_='page-count').span.text
    for j in range(int(page_count)):
        # 暂时不需要下载太多---------------------------------------------------------------
        if j > MAX_MANY_IMAGE_COUNT:
            break
        f = filename.replace('.', '-' + str(j) + '.')
        p = '_p' + str(j) + '_'
        large_jpg_url = small_jpg_url.replace(r'c/240x480/', '').replace('_p0_', p)
        large_png_url = large_jpg_url.replace('jpg', 'png')
        downloadImage(downloadpath, f, large_jpg_url, large_png_url, login_req,image_url)


# 动图抓取
def gifImageCrawl(small_jpg_url, filename, login_req,image_url):
    downloadpath = getdownloadPath(GIF_DOWNLOAD_PATH)
    gif_url = small_jpg_url.replace(r'c/240x480/img-master', 'img-zip-ugoira').replace('_master1200.jpg', '_ugoira600x600.zip')
    downloadGif(downloadpath, filename, gif_url, login_req,image_url)


# 动图下载
def downloadGif(downloadpath, filename, gifurl, login_req,image_url):
    fullpath = os.path.join(downloadpath, filename)
    gif = login_req.head(url=gifurl, headers=headers)
    if not isImageExist(fullpath):
        if gif.status_code == 200:
            print('动图下载开始%s' % filename)
            s = datetime.now().timestamp()
            gif_downloader.downloader(login=login_req, url=gifurl, num=THREAD_COUNT, filename=fullpath,referer=image_url).run()
            e = datetime.now().timestamp()
            print('动图下载结束 , 耗时 %.2f 秒 , 文件大小 %.2f KB , 平均下载速度 %.2f KB/S' % ((e - s), (os.path.getsize(fullpath) / 1024), (os.path.getsize(fullpath) / 1024 / (e- s))))
        else:
            print('无法找到该动图!!!')
    else:
        print('动图已存在!!')


# 图片下载
def downloadImage(downloadpath, filename, jpgurl, pngurl, login_req,image_url):
    fullpath = os.path.join(downloadpath, filename)
    jpg = login_req.head(url=jpgurl, headers=headers)
    png = login_req.head(url=pngurl, headers=headers)
    if not isImageExist(fullpath):
        if jpg.status_code == 200:
            print('图片下载开始%s' % filename)
            s = datetime.now().timestamp()
            gif_downloader.downloader(login=login, url=jpgurl, num=THREAD_COUNT, filename=fullpath,referer=image_url).run()
            e = datetime.now().timestamp()
            print('图片下载结束 , 耗时 %.2f 秒 , 文件大小 %.2f KB , 平均下载速度 %.2f KB/S' % ((e - s), (os.path.getsize(fullpath) / 1024), (os.path.getsize(fullpath) / 1024 / (e- s))))
        elif png.status_code == 200:
            print('图片下载开始%s' % filename)
            s = datetime.now().timestamp()
            gif_downloader.downloader(login=login, url=pngurl, num=THREAD_COUNT, filename=fullpath,referer=image_url).run()
            e = datetime.now().timestamp()
            print('图片下载结束 , 耗时 %.2f 秒 , 文件大小 %.2f KB , 平均下载速度 %.2f KB/S' % ((e - s), (os.path.getsize(fullpath) / 1024), (os.path.getsize(fullpath) / 1024 / (e- s))))
        else:
            print('无法找到该图片!!!')
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
    for i in range(items_length):
        curr_dom = items[i]
        image_url = 'https://www.pixiv.net' + curr_dom.find(class_='ranking-image-item').a.get('href')
        data_src = curr_dom.find('img').get('data-src')
        print(data_src)
        headers['Referer'] = image_url
        image_id = re.search(re_filename, image_url).group()
        if getImageType(data_src) == 'image':
            filename = image_id + '.jpg'
            if isSingleImage(curr_dom):
                singleImageCrawl(data_src, filename, login,image_url)
            else:
                manyImageCrawl(data_src, filename, curr_dom, login,image_url)
        elif getImageType(data_src) == 'gif':
            filename = image_id + '.zip'
            gifImageCrawl(data_src, filename, login,image_url)
        else:
            print('没有这种格式的图片!!')
