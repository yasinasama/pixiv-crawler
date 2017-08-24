import requests, requests.adapters
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
import file_downloader
import queue
import threading
import logging

MAX_RANK_PAGE = 10  # 排行榜页数 最多10页
MAX_EACH_PAGE = 1  # 每页图片数 最多50张
MAX_MANY_IMAGE_COUNT = 5  # 多图中抓取数
GIF_DOWNLOAD_PATH = 'd:\pixiv\gif'  # 动图存放地址

today = datetime.strftime(datetime.date(datetime.now()), '%Y%m%d')
DOWNLOAD_PATH = os.path.join('d:\pixiv', today)
THREAD_COUNT = 20  # 线程数
POOL_MAXSIZE = 20 * 20  # 下载线程数和单图下载线程数 20*20
TIMEOUT = 10  # 连接超时时间 最好都设置，不然有可能程序无响应
URL_QUEUE = queue.Queue()  # 图片URL队列
re_filename = re.compile('(\d+)')

logging.basicConfig(level=logging.INFO)
# 排行榜模式
# --------------------------
# daily    每日
# weekly   每周
# monthly  每月
# rookie   新人
# original 原创
# male     受男性喜欢
# female   受女性喜欢
# ------------------------------------
MODE_LIST = {
    '1': 'daily',
    '2': 'weekly',
    '3': 'monthly',
    '4': 'rookie',
    '5': 'original',
    '6': 'male',
    '7': 'female'
}
# 下载图片类型
# --------------------------
# ''         综合
# illust     插画
# ugoira     动图
# ------------------------------------
CONTENT_LIST = {
    '1': '',  # 综合
    '2': 'illust',  # 插画
    '3': 'ugoira',  # 动图
}
# Referer   防盗链
# Range     断点获取响应内容
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36',
    'Referer': '',
    'Range': ''
}
# get参数
param = {
    'mode': '',
    'date': '',
    'content': ''
}
# post参数
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


# 获取当前下载文件文件夹大小
def getDirSize():
    dir_size = 0
    for i in os.listdir(DOWNLOAD_PATH):
        dir_size += os.path.getsize(os.path.join(DOWNLOAD_PATH, i))
    return dir_size


# 获取下载文件保存路径
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


# 图片 GIF？
def getImageType(image_src):
    if image_src.find('_p0') > 0:
        return 'image'
    else:
        return 'gif'


# 处理登录 返回登录session
def loginPixiv():
    pixiv_id = input('请输入账号: ')
    password = input('请输入密码: ')
    # 获取session实例
    p = requests.Session()
    # 多线程下pool_maxsize 小于你的线程值
    p.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=POOL_MAXSIZE))
    # 获取post请求必要数据
    p.headers = headers
    r = p.get(url='https://accounts.pixiv.net/login', headers=headers, timeout=TIMEOUT)
    parrern = re.compile(r'name="post_key" value="(.*?)">')
    res = parrern.search(r.text)
    data['post_key'] = res.group()
    data['pixiv_id'] = pixiv_id
    data['password'] = password

    # post请求模拟登陆
    logging.info('模拟登陆开始......')
    try:
        p.post(url='https://accounts.pixiv.net/api/login', data=data, timeout=TIMEOUT)
        logging.info('模拟登陆成功......')
        return p
    except:
        logging.warning('模拟登陆失败......')
        raise


# 获取用户指定下载页面URL
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
            logging.warning('请正确输入!!!')
            continue
        date = input('请输入日期:  例如20170101 -----------  ')

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
            logging.warning('输入日期必须早于当前日期!!!!')


# 动图URL收集
def collectGifUrl(image_src, image_id, login):
    image_name, image_url = '', ''
    gif_url = image_src.replace(r'c/240x480/img-master', 'img-zip-ugoira').replace('_master1200.jpg', '_ugoira600x600.zip')
    gif = login.head(url=gif_url, headers=headers, timeout=TIMEOUT)
    if gif.status_code == 200:
        image_name = image_id + '.zip'
        image_url = gif_url
    else:
        logging.warning('无法找到该动图!!!')

    return image_name, image_url


# 图片URL收集
def collectImageUrl(dom, image_src, image_id, login):
    image_name, image_url = '', ''
    # 单张图
    if isSingleImage(dom):
        image_jpg_url = image_src.replace(r'c/240x480/img-master', 'img-original').replace('_master1200', '')
        image_png_url = image_jpg_url.replace('jpg', 'png')
        jpg = login.head(url=image_jpg_url, headers=headers, timeout=TIMEOUT)
        png = login.head(url=image_png_url, headers=headers, timeout=TIMEOUT)
        if jpg.status_code == 200:
            image_name = image_id + '.jpg'
            image_url = image_jpg_url

        elif png.status_code == 200:
            image_name = image_id + '.png'
            image_url = image_png_url
        else:
            logging.warning('无法找到该图片!!!')
    # 多张图
    else:
        image_count = dom.find(class_='page-count').span.text
        for j in range(int(image_count)):
            if j > MAX_MANY_IMAGE_COUNT:
                break
            p = '_p' + str(j) + '_'
            image_jpg_url = image_src.replace(r'c/240x480/', '').replace('_p0_', p)
            image_png_url = image_jpg_url.replace('jpg', 'png')
            jpg = login.head(url=image_jpg_url, headers=headers, timeout=TIMEOUT)
            png = login.head(url=image_png_url, headers=headers, timeout=TIMEOUT)
            if jpg.status_code == 200:
                image_name = image_id + '.jpg'.replace('.', '-' + str(j) + '.')
                image_url = image_jpg_url
            elif png.status_code == 200:
                image_name = image_id + '.png'.replace('.', '-' + str(j) + '.')
                image_url = image_png_url
            else:
                logging.warning('无法找到该图片!!!')

    return image_name, image_url


# 多线程下载图片（队列消费）
def downLoad(login):
    while not URL_QUEUE.empty():
        file, ref, url = URL_QUEUE.get()
        logging.info('%s   %s   %s' % (file, ref, url))
        file_downloader.downloader(login, url, THREAD_COUNT, file, ref).run()
        URL_QUEUE.task_done()


# 获取待下载图片（高清大图-0-）URL
def getReadyCrawlUrl(login):
    s = datetime.now()
    list = getCrawlUrl()
    path = getdownloadPath(DOWNLOAD_PATH)
    for url in list:
        try:
            result = login.get(url=url, headers=headers, timeout=TIMEOUT)
        except Exception as e:
            logging.exception(e)
            raise
        # 获取我们分析的主要的DOM节点信息
        soup = BeautifulSoup(result.text, "html.parser")
        items = soup.find_all(class_='ranking-item')
        for i in items:
            referer_url = 'https://www.pixiv.net' + i.find(class_='ranking-image-item').a.get('href')
            image_src = i.find('img').get('data-src')
            image_id = re.search(re_filename, referer_url).group()
            print(image_src)
            headers['Referer'] = referer_url
            if getImageType(image_src) == 'image':
                try:
                    co = collectImageUrl(i, image_src, image_id, login)
                except Exception as e:
                    logging.exception(e)
                    continue
                if co[0] != '' and co[1] != '':
                    image_path = os.path.join(path, co[0])
                    if not isImageExist(image_path):
                        URL_QUEUE.put([image_path, referer_url, co[1]])
                    else:
                        logging.warning('图片已存在')
                        continue
            elif getImageType(image_src) == 'gif':
                co = collectGifUrl(image_src, image_id, login)
                if co[0] != '' and co[1] != '':
                    image_path = os.path.join(path, co[0])
                    if not isImageExist(image_path):
                        URL_QUEUE.put([image_path, referer_url, co[1]])
                    else:
                        logging.warning('动图已存在')
                        continue
            else:
                logging.warning('暂时不支持此类型！！')
    logging.info('总计用时 %d 秒' % (datetime.now() - s).seconds)


# do
def do(login):
    s = datetime.now()
    t = []
    for i in range(THREAD_COUNT):
        th = threading.Thread(target=downLoad, args=(login,))
        t.append(th)

    for i in t:
        i.start()

    for i in t:
        i.join()

    URL_QUEUE.join()

    use = (datetime.now() - s).seconds
    size = getDirSize()
    logging.info('总计用时 %d 秒，平均下载速度 %d KB/S' % (use, size / use / 1024))


if __name__ == '__main__':
    login = loginPixiv()
    getReadyCrawlUrl(login)
    do(login)
