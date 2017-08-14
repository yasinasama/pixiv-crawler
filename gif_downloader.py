import threading


class downloader:
    def __init__(self, login, url, num, filename,referer):
        self.url = url
        self.num = num
        self.login = login
        self.lock = threading.Lock()
        self.filename = filename
        self.referer = referer
        self.total = int(self.login.head(self.url).headers['Content-Length'])

    def get_range(self):
        ranges = []
        offset = int(self.total / self.num)
        for i in range(self.num):
            if i == self.num - 1:
                ranges.append((i * offset, self.total - 1))
            else:
                ranges.append((i * offset, (i + 1) * offset - 1))
        return ranges

    def download(self, start, end, f):
        retry = 0
        success = False
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36',
            'Referer': '%s' % self.referer,
            'Range': 'Bytes=%s-%s' % (start, end)
        }
        while retry<3 and not success:
            try:
                res = self.login.get(self.url, headers=headers)
                success = True
            except Exception as e:
                print(e)
                retry+=1
                if retry==3:
                    break
        if success:
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
