import asyncio
import os
import re
# import time
import typing
import tomd
import puppeteer
# import execjs  # pip install PyExecJS
import requests
from urllib.parse import urlparse
from pyquery import PyQuery as pq
from dataclasses import dataclass, field

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
}

@dataclass
class Wanted:
    img_tag: str = "img"
    selector: str = ".content"
    title: typing.Callable = lambda q: q("title").text().split("-")[0]
    find_img: typing.Callable = lambda q: q.attr('src')
    page_source: typing.Callable = lambda url, selector: pq(url=url,
                                                            opener=lambda url, **kw: requests.get(url,
                                                                                                  headers=headers).content)

    def pathed(self, p):
        pattern = "[`~!@#$%^&-+=\\?:\"|,/;'\\[\\]·~！@#￥%……&*（）+=\\{\\}\\|《》？：“”【】、；‘'，。\\、\\-\s]"
        return re.sub(pattern, "", p)

    # 保存md文件;
    def save_md(self, title, md_txt):
        title = self.pathed(title)
        save_path = './' + title
        if not os.path.exists(save_path):
            os.mkdir(save_path)  # 如果本文档目录不存在, 就创建;
        # 保存文件;
        with open(save_path + '/' + title + ".md", 'w', encoding='utf-8') as f:
            f.write(md_txt)

    # 保存图片;
    def save_pic(self, org_url, title, index, url) -> str:
        blog_url = urlparse(org_url)
        img_url = ""
        if url.startswith("http://") or url.startswith("https://"):
            img_url = url
        elif url.startswith("//"):
            img_url = blog_url.scheme + ":" + url
        else:
            if url.startswith("/"):
                img_url = blog_url.scheme + "://" + blog_url.netloc + url
            else:
                sp = blog_url.path.split("/")
                img_url = blog_url.scheme + "://" + blog_url.netloc + blog_url.path.replace(sp[len(sp) - 1], "") + url

        title = self.pathed(title)
        img_name = title + "_" + str(index) + ".jpg"
        save_path = './' + title + "/img"
        if not os.path.exists(save_path):
            os.makedirs(save_path)  # 如果本文档目录不存在, 就创建;
        img_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
            'Referer': blog_url.scheme + "://" + blog_url.netloc
        }
        # 保存图片文件;
        with open(save_path + '/' + img_name, 'wb') as f:
            f.write(requests.get(img_url, headers=img_headers).content)
        return "img/" + img_name

class Html2md:
    def __init__(self, url, title="", selector=""):
        self.url = url
        self.title = title
        self.selector = selector
        self.rule = self.get_rule(self.url)
        if not self.selector:
            self.selector = self.rule.selector
        # get加载页面;
        self.rootQ = self.rule.page_source(self.url, self.selector)
        if not self.title:
            self.title = self.rule.title(self.rootQ)

    # 获取url规则;
    def get_rule(self, url=""):
        if not url:
            url = self.url
        if "www.cnblogs.com" in url:
            return Wanted(selector="#cnblogs_post_body")
        if "segmentfault.com" in url:
            return Wanted(selector=".article.fmt.article-content", find_img=lambda q: q.attr('data-src'))
        if "blog.csdn.net" in url:
            return Wanted(selector="#content_views")
        if "www.jianshu.com" in url:
            return Wanted(selector="article", find_img=lambda q: q.attr('data-original-src'))
        if "mp.weixin.qq.com" in url:
            return Wanted(selector="#js_content", find_img=lambda q: q.attr('data-src'))
        if "www.oschina.net" in url:
            return Wanted(selector=".article-detail")
        if "cloud.tencent.com" in url:
            return Wanted(selector=".com-markdown-collpase", img_tag="span.lazy-image-holder",
                          find_img=lambda q: q.attr('dataurl'))
        if "zhuanlan.zhihu.com" in url:
            return Wanted(selector=".Post-RichTextContainer", find_img=lambda q: q.attr('data-actualsrc'))
        if "www.toutiao.com" in url or "m.toutiao.com" in url:
            return Wanted(selector=".article-box", page_source=puppeteer.get_page_source)
        return Wanted()

    # 转换;
    def convert(self, name="", selector=""):
        if not name:
            name = self.title
        if not selector:
            selector = self.selector
        # 提取文章内容;
        contentQ = self.rootQ(selector)
        # 处理图片;
        index = 1
        for e in contentQ(self.rule.img_tag):
            q = pq(e)
            img_src = self.rule.find_img(q)
            img_src_cur = self.rule.save_pic(self.url, name, index, img_src)
            if q[0].tag != "img":
                q.replace_with(pq('<img src="' + img_src_cur + '"/>'))
            else:
                q.attr(src=img_src_cur)
            index += 1
        # 转换成markdown;
        self.rule.save_md(name, tomd.convert(contentQ))


import argparse

parser = argparse.ArgumentParser(description='url to markdown.')
parser.add_argument('urls', metavar='url', type=str, nargs='+',
                    help='需要转换的url地址')
parser.add_argument('--name', "-n", help='保存的文件名', required=False)
parser.add_argument('--selector', "-s", help='post内容选择器', required=False)
args = parser.parse_args()

if "__main__" == __name__:
    if len(args.urls) == 1:
        Html2md(args.urls[0]).convert(name=args.name, selector=args.selector)
    else:
        for url in args.urls:
            Html2md(url).convert()
