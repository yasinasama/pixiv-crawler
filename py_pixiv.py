import requests
from bs4 import BeautifulSoup
import re


header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36   '
}

params = {
    # 'lang': 'zh',
    # 'source': 'pc',
    # 'view_type': 'page',
    'Referer': 'https://www.pixiv.net/'
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

# 国际排行榜URL
RANK_AREA = 'https://www.pixiv.net/ranking.php?mode=monthly'

# 获取session实例
p = requests.Session()

# 获取post请求必要数据
p.headers = header
r = p.get(url='https://accounts.pixiv.net/login', params=params)
parrern = re.compile(r'name="post_key" value="(.*?)">')
res = parrern.search(r.text)
data['post_key'] = res.group()

# post请求模拟登陆
p.post(url='https://accounts.pixiv.net/api/login', data=data)
result = p.get(url=RANK_AREA)


soup = BeautifulSoup(result.text, "html.parser")
items = soup.find_all(class_='ranking-item')
items_length = len(items)
old_jpgs = [items[i].find('img').get('data-src') for i in range(items_length)]
new_jpgs = [jpg.replace(r'c/240x480/img-master', 'img-original').replace('_master1200','') for jpg in old_jpgs]
new_pngs = [jpg.replace('jpg', 'png') for jpg in new_jpgs]
[print(jpg) for jpg in new_jpgs]


print(requests.get('https://i.pximg.net/img-original/img/2017/08/05/20/04/20/64239362_p0.png', params=params).status_code)
for i in range(3):
    # print(p.get('https://i.pximg.net/img-original/img/2017/08/05/20/04/20/64239362_p0.png', params=params).status_code)
    if p.get(url=new_jpgs[i], params=params).status_code == '200':
        print(new_jpgs[i]+' is JPG!')
    elif p.get(url=new_pngs[i], params=params).status_code == '200':
        print(new_pngs[i]+' is PNG!')
    else:
        print('NOT FOUND!')