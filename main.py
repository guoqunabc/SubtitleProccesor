import os
import sys
import math
import time
import json
import uuid
import requests
import hashlib


class SrtRevisor:
    def __init__(self):
        self.number = []
        self.timeline = []
        self.chinese = []
        self.english = []
        self.cache = []
        self.TIME_SEP = ' --> '
        self.translator = Translator()

    def process_line(self, line):
        line = line.strip('\n').strip()
        if len(line) == 0:
            self.process_cache()
        else:
            self.cache.append(line)

    def process_cache(self):
        if len(self.cache) == 4:
            self.number.append(self.cache[0])
            self.timeline.append(self.cache[1])
            self.chinese.append(self.cache[2])
            self.english.append(self.cache[3])
        elif len(self.cache) > 4:
            print(self.cache)
            raise ValueError
        self.cache = []

    def read_file(self, path):
        with open(path, 'r', encoding='UTF-8') as f:
            lines = f.readlines()
            for line in lines:
                self.process_line(line)
        print('Srt File Loaded!')

    def print_len(self):
        print('self.number: ', len(self.number))
        print('self.timeline: ', len(self.timeline))
        print('self.chinese: ', len(self.chinese))
        print('self.english: ', len(self.english))

    def revise_num(self):
        length = len(self.number)
        self.number = [str(_) for _ in range(1, length + 1)]

    def str2time(self, time_str):
        t = time_str.split(',')
        t_0, t_1 = t[0].split(':'), [t[1]]
        t = t_0 + t_1
        t = [int(_) for _ in t]
        time_sec = 3600 * t[0] + 60 * t[1] + t[2] + t[3] / 1000
        return time_sec

    def time2str(self, time_sec):
        time_list = [0, 0, 0, 0]
        t = math.modf(time_sec)
        t_0, t_1 = int(t[0] * 1000), t[1]
        time_list[3] = t_0
        time_list[0] = math.floor(t_1 / 3600)
        t_1 = t_1 % 3600
        time_list[1] = math.floor(t_1 / 60)
        t_1 = t_1 % 60
        time_list[2] = math.floor(t_1)
        return '%02d:%02d:%02d,%03d' % (time_list[0], time_list[1], time_list[2], time_list[3])

    def revise_time(self):
        time_line = []
        for timestep in self.timeline:
            t_s, t_e = [self.str2time(_) for _ in timestep.split(self.TIME_SEP)]
            time_line.append(t_s)
            time_line.append(t_e)
        length_t = len(time_line)
        count = 0
        while count < length_t - 1:
            if time_line[count] > time_line[count + 1]:
                time_line[count] = time_line[count + 1]
            count += 1
        count = 0
        while count < length_t - 2:
            time_line[count + 1] = time_line[count + 2] - 0.03
            count += 2
        count = 0
        while count < length_t - 1:
            t_s = self.time2str(time_line[count])
            t_e = self.time2str(time_line[count + 1])
            t_str = '%s%s%s' % (t_s, self.TIME_SEP, t_e)
            self.timeline[math.floor(count / 2)] = t_str
            count += 2

    def revise_all(self):
        self.revise_num()
        self.revise_time()

    def translate(self, start=0, end=None):
        length = len(self.number)
        if end is None:
            end = length
        count = start
        while count < end:
            self.chinese[count] = self.translator.connect(self.english[count])
            count += 1
            time.sleep(0.5)
        print('Translate complete!')

    def write_file(self, path):
        with open(path, 'w', encoding='UTF-8') as f:
            length = len(self.number)
            count = 0
            while count < length:
                f.write(self.number[count] + '\n')
                f.write(self.timeline[count] + '\n')
                f.write(self.chinese[count] + '\n')
                f.write(self.english[count] + '\n')
                f.write('\n')
                count += 1
        print('Revised Srt File Created!')


class Translator:
    def __init__(self):
        self.API = 'http://openapi.youdao.com/api'
        self.header = {}
        self.APP_KEY = '3d427783a4e1ba7d'
        self.APP_SECRET = 'NVWeIqTR1vHObxNclVYcvLqj6HidkYwN'

    def encrypt(self, signStr):
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(signStr.encode('utf-8'))
        return hash_algorithm.hexdigest()

    def truncate(self, q):
        if q is None:
            return None
        size = len(q)
        return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

    def do_request(self, data):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        return requests.post(self.API, data=data, headers=headers)

    def connect(self, q):
        data = {}
        data['from'] = 'EN'
        data['to'] = 'zh-CHS'
        data['signType'] = 'v3'
        curtime = str(int(time.time()))
        data['curtime'] = curtime
        salt = str(uuid.uuid1())
        signStr = self.APP_KEY + self.truncate(q) + salt + curtime + self.APP_SECRET
        sign = self.encrypt(signStr)
        data['appKey'] = self.APP_KEY
        data['q'] = q
        data['salt'] = salt
        data['sign'] = sign

        response = self.do_request(data)
        # print(response.content)
        res = json.loads(response.text)['translation']
        print(res)
        return res[0]


if __name__ == '__main__':
    ROOT = os.getcwd()
    file_path = os.path.join(ROOT, 'data', 'version2.0.txt')
    save_path = os.path.join(ROOT, 'result', 'version2.1.txt')
    srt_obj = SrtRevisor()
    srt_obj.read_file(file_path)
    srt_obj.print_len()
    srt_obj.revise_all()
    srt_obj.translate(15)
    srt_obj.write_file(save_path)
