# LmPixivCrawl
Crawl the images from Pixiv with Python

碰到的问题：
  1. 登录需要post_key，post_key在登录页面源码中能找到，所以需要一开始请求一次登录页面。之后的操作都保证在登录session下操作
  2. p站大图存在防盗链，需要在headers中加入Referer：url(点击进入图片的那个URL)  只要在P站上面获取图片资料都需要指定referer
  3. 多图链接我按照单图的URL转换也能抓取(不采用)
  4. 排行榜最多500张  也就是说param P<=10
        5.黑白图片过滤，我想你可能不需要这种图片吧
        6.动图的获取
         6.1  P站动图都是通过请求zip（里面是每一帧的图像）
         6.2  zip很大，单线程下载慢  采用多线程   stream=TRUE  有点问题
         6.3  多线程共享变量要格外注意啊