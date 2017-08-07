# LmPixivCrawl
Crawl the images from Pixiv with Python

碰到的问题：
  1. 登录需要post_key，post_key在登录页面源码中能找到，所以需要一开始请求一次登录页面。
  2. p站大图存在防盗链，需要在headers中加入Referer：url(点击进入图片的那个URL)
  3.多图链接我按照单图的URL转换也能抓取
