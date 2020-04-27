from bs4 import BeautifulSoup
from requests import get, post
from requests.exceptions import ConnectionError
from urllib.parse import urlsplit, urlparse, parse_qs
from time import sleep, time
from warnings import warn
from os import system, name
import re
import configparser
import schedule


def get_domain(url):
    domain = "{0.scheme}://{0.netloc}/".format(urlsplit(url))
    return domain.rsplit('/', 1)[0]


def get_query(url, param):
    try:
        parsed = urlparse(url)
        return parse_qs(parsed.query)[param][0]
    except:
        return None


def get_search_str(contents, mathed):
    try:
        reg = mathed + '(\s)?：([\u4e00-\u9fff\uff01-\uff150-9\s〔〕.*-a-zA-Z\(\)]+)<br/>'
        p = re.compile(reg)
        m = p.search(str(contents))
        return remove_space(m.groups()[1])
    except Exception as e:
        print('error', e)
        return ""


def get_search_el(el, tag, word):
    try:
        element = el(tag, text=re.compile(word))[0]
        text_content = get_txt(element).split(word)[1]
        return remove_space(text_content)
    except:
        return ""


def get_txt(string):
    try:
        return string.get_text(strip=True)
    except:
        return ""


def get_param(el, param):
    try:
        return el[param]
    except:
        return ""


def word_split(string, index):
    return string.rsplit('->', 1)[index]


def get_number(string):
    return re.findall(r'[\d.]+', string)[0]


def remove_space(string):
    return "".join(string.split())


def srcrepl(match):
    old_link = match.group(3)
    origin_url = ""
    try:
        effect_link = old_link.rsplit('../', 1)[1]
        pre_count = len(re.findall(r"..\/", old_link))
        absolutePath = url_split(origin_url, pre_count, 0) + '/' + effect_link
        print(absolutePath)
        return "<" + match.group(1) + match.group(
            2) + "=" + "\"" + absolutePath + "\"" + match.group(4) + "\"" + ">"
    except:
        effect_link = old_link.rsplit('./', 1)[1]
        pre_count = len(re.findall(r".\/", old_link))
        absolutePath = url_split(origin_url, pre_count, 0) + '/' + effect_link
        print(absolutePath)
        return "<" + match.group(1) + match.group(
            2) + "=" + "\"" + absolutePath + "\"" + match.group(4) + "\"" + ">"


def update_links(fileContents):
    p = re.compile(r"<(.*?)(src|href)=\"(?!http)((?!javascript).*?)\"(.*?)>")
    return p.sub(srcrepl, fileContents)
