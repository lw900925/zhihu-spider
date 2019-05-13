# -*- coding:utf-8 -*-

# 声明：知乎上某个答主写的爬虫脚本，代码没有整理，自己重新整理排版了，已经调试并通过
#      本人Java程序员，对python不熟，不过代码里面逻辑大概能看懂一些，这位答主的脚本是python2写的，
#      我自己是python3的环境，所以有些细微的改动，目的是为了兼容python3可以正常运行
#
#      原始脚本地址：https://www.zhihu.com/question/297715922/answer/676693318
#      如果觉得我冒犯了你的话，可以私信联系我，我删除。

import re
import requests
import os
import urllib.request
import ssl

from urllib.parse import urlsplit
from os.path import basename

# 全局禁用证书验证
ssl._create_default_https_context = ssl._create_unverified_context

headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
    'Accept-Encoding': 'gzip, deflate'
}

# 下载出错的列表
failed_image_list = []


def mkdir(path):
    if not os.path.exists(path):
        print('新建文件夹：', path)
        os.makedirs(path)
        return True
    else:
        print(u"图片存放于：", os.getcwd() + os.sep + path)
        return False


def download_pic2(img_lists, dir_name):
    print("一共有{num}张照片".format(num=len(img_lists)))

    # 标记下载进度
    index = 1

    for image_url in img_lists:
        file_name = dir_name + os.sep + basename(urlsplit(image_url)[2])

        # 已经下载的文件跳过
        if os.path.exists(file_name):
            print("文件{file_name}已存在。".format(file_name=file_name))
            index += 1
            continue

        # 重试次数
        retry_time = 3
        auto_download(image_url, file_name, retry_time)

        print("下载{pic_name}完成！({index}/{sum})".format(pic_name=file_name, index=index, sum=len(img_lists)))
        index += 1

    # 打印下载出错的文件
    if len(failed_image_list):
        print("以下文件下载失败：")
        for failed_image_url in failed_image_list:
            print(failed_image_url)


def auto_download(image_url, file_name, retry_time):
    # 递归下载，直到文件下载成功
    try:
        # 判断剩余下载次数是否小于等于0，如果是，就跳过下载
        if retry_time <= 0:
            print("下载失败，请检查{image_url}链接是否正确（必要时可以手动下载）")
            failed_image_list.append(image_url)
            return

        # 下载文件
        urllib.request.urlretrieve(image_url, file_name)

    except urllib.request.ContentTooShortError:
        print("文件下载不完整，尝试重新下载，剩余尝试次数{retry_time}".format(retry_time=retry_time))
        retry_time -= 1
        auto_download(image_url, file_name, retry_time)

    except urllib.request.URLError as e:
        print("网络连接出错，尝试重新下载，剩余尝试次数{retry_time}".format(retry_time=retry_time))
        retry_time -= 1
        auto_download(image_url, file_name, retry_time)


def download_pic(img_lists, dir_name):
    print("一共有{num}张照片".format(num=len(img_lists)))
    for image_url in img_lists:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            image = response.content
        else:
            continue

        file_name = dir_name + os.sep + basename(urlsplit(image_url)[2])

        try:
            with open(file_name, "wb") as picture:
                picture.write(image)
        except IOError:
            print("IO Error\n")
            continue
        finally:
            picture.close()

        print("下载{pic_name}完成！".format(pic_name=file_name))


def get_image_url(qid, headers, path):
    # 利用正则表达式把源代码中的图片地址过滤出来
    # reg = r'data-actualsrc="(.*?)">'
    tmp_url = "https://www.zhihu.com/node/QuestionAnswerListV2"
    offset = 0
    image_urls = []

    session = requests.Session()

    # 答案数
    answer_num = 0

    while True:
        postdata = {'method': 'next',
                    'params': '{"url_token":' + str(qid) + ',"pagesize": "10","offset":' + str(offset) + "}"}
        page = session.post(tmp_url, headers=headers, data=postdata)
        ret = eval(page.text)
        answers = ret['msg']
        
        offset += 10

        if not answers:
            print("图片URL获取完毕, 页数: ", (offset - 10) / 10)
            return image_urls

        answer_num += len(answers)

        # reg = r'https://pic\d.zhimg.com/[a-fA-F0-9]{5,32}_\w+.jpg'
        imgreg = re.compile('data-original="(.*?)"', re.S)

        for answer in answers:
            tmp_list = []
            url_items = re.findall(imgreg, answer)

            for item in url_items:  # 这里去掉得到的图片URL中的转义字符'\\'
                image_url = item.replace("\\", "")
                tmp_list.append(image_url)

            # 清理掉头像和去重 获取data-original的内容
            tmp_list = list(set(tmp_list))  # 去重
            for item in tmp_list:
                if item.endswith('r.jpg'):
                    print(item)
                    write_image_url_to_file(path, item)
                    image_urls.append(item)

        print('offset: %d, num : %d' % (offset, len(image_urls)))
    
    # 打印答案数
    print(u"答案数：%d" % (len(answers)))


def write_image_url_to_file(file_name, image_url):
    file_full_name = file_name + '.txt'

    f = open(file_full_name, 'a')
    f.write(image_url + '\n')
    f.close()


def read_image_url_from_file(file_name):
    file_full_name = file_name + '.txt'

    # 文件下载链接列表
    image_url_list = []

    # 判断文件是否存在
    if not os.path.exists(file_full_name):
        return image_url_list

    with open(file_full_name, 'r') as f:
        for line in f:
            line = line.replace("\n", "")
            image_url_list.append(line)

    print("从文件中读取下载链接完毕，总共有{num}个文件".format(num=len(image_url_list)))
    return image_url_list


if __name__ == '__main__':
    # title = '拥有一副令人羡慕的好身材是怎样的体验？'
    # question_id = 297715922

    # title = '身材好是一种怎样的体验？'
    # question_id = 26037846

    # title = '女孩子胸大是什么体验？'
    # question_id = 291678281

    # title = '女生什么样的腿是美腿？'
    # question_id = 310786985

    # title = '你的择偶标准是怎样的？'
    # question_id = 275359100

    # title = '什么样才叫好看的腿？'
    # question_id = 63727821

    # title = '身材对女生很重要吗？'
    # question_id = 307403214

    # title = '女生腿长是什么样的体验？'
    # question_id = 273711203

    # title = '女生腕线过裆是怎样一种体验？'
    # question_id = 315236887

    # title = '有着一双大长腿是什么感觉？'
    # question_id = 292901966

    # title = '拥有一双大长腿是怎样的体验？'
    # question_id = 285321190

    # title = '大胸女生如何穿衣搭配？'
    # question_id = 26297181

    # title = '胸大到底怎么穿衣服好看'
    # question_id = 293482116

    # title = '现在只要是胖女生都没有人追吗？'
    # question_id = 315434636

    # title = '你的日常搭配是什么样子？'
    # question_id = 35931586

    # title = '女生穿成这样真的算暴露吗？'
    # question_id = 321123412

    # title = '那些传说中超好看的腿型都是什么样子的？'
    # question_id = 273647787

    title = '当你有一双好看的腿之后，会不会觉得差一张好看的脸？'
    question_id = 266695575

    # title = '身高一米58，体重120斤是不是真的很胖？'
    # question_id = 320606641

    zhihu_url = "https://www.zhihu.com/question/{qid}".format(qid=question_id)
    path = str(question_id) + '_' + title
    mkdir(path)  # 创建本地文件夹

    # 优先从文件中读取下载列表
    img_list = read_image_url_from_file(path)
    if not len(img_list):
        # 获取图片的地址列表
        img_list = get_image_url(question_id, headers, path)

    # 下载文件
    download_pic2(img_list, path)