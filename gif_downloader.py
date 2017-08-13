import threading


class downloader:
    def __init__(self, login, url, num,filename):
        self.url = url
        self.num = num
        self.login = login
        self.lock = threading.Lock()
        self.filename = filename
        r = self.login.head(self.url)
        self.total = int(r.headers['Content-Length'])
        print('文件大小: %.2f M' % (self.total / 1024 / 1024))

    def get_range(self):
        ranges = []
        offset = int(self.total / self.num)
        for i in range(self.num):
            if i == self.num - 1:
                ranges.append((i * offset, self.total - 1))
            else:
                ranges.append((i * offset, (i + 1) * offset - 1))
        return ranges

    def download(self, start, end,f):
        headers = {'Range': 'Bytes=%s-%s' % (start, end)}
        res = self.login.get(self.url, headers=headers)
        with self.lock:
            f.seek(start)
            f.write(res.content)

    def run(self):
        fn = open(self.filename, "wb")
        thread_list = []
        for ran in self.get_range():
            start, end = ran
            thread = threading.Thread(target=self.download, args=(start, end, fn))
            thread_list.append(thread)

        for i in thread_list:
            i.start()

        for i in thread_list:
            i.join()

        fn.close()



