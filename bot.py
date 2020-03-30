from bs4 import BeautifulSoup
from requests import get, post
from requests.exceptions import ConnectionError
import re
import json
import configparser
from time import sleep, time
from datetime import datetime, timedelta
from random import randint
from warnings import warn
from collections import namedtuple
import utils
import schedule
from os import system, name 

configParser = configparser.RawConfigParser()
configParser.read('config.ini')
CSV_PATH = configParser.get('LOCAL', 'CSV_DIR')
FILE_PATH = configParser.get('LOCAL', 'FILE_DIR')
log_status = {}
error_count = 0

base_urls = [
    { "level": "procurement", "category": "tender_notices", "url": "http://www.ccgp-guangdong.gov.cn/queryMoreInfoList.do?channelCode=0005&pageSize=30" },
    { "level": "procurement", "category": "correction_notices", "url": "http://www.ccgp-guangdong.gov.cn/queryMoreInfoList.do?channelCode=0006&pageSize=30" },
    { "level": "procurement", "category": "deal_notices", "url": "http://www.ccgp-guangdong.gov.cn/queryMoreInfoList.do?channelCode=0008&pageSize=30" },
    { "level": "procurement", "category": "county_notices", "url": "http://www.ccgp-guangdong.gov.cn/queryMoreCityCountyInfoList2.do?channelCode=00051&pageSize=30"},
]


field_names = {
    "all": ['title', 'region', 'source', 'procurement_number', 'item_name', 'deal_price', 'agency', 'responsible_person', 'project_manager', 'publisher', 'published_date', 'source_url', 'id'],
    "sub": ['title', 'category', 'publish_date', 'source_url', 'id']
}

headers = {"Accept-Language": "en-US, en;q=0.5", "User-Agent":"Mozilla/5.0"}


# Preparing the monitoring of the loop
start_time = time()


class links:
    def __init__(self, title, url, date, region):
        self.title = title
        self.url = url
        self.date = date
        self.region = region

class Contracts:
    def __init__(self):
        self.region = ''
        self.title = ''
        self.source = ''
        self.procurement_number = ''
        self.item_name = ''
        self.deal_price = ''
        self.agency = ''
        self.responsible_person = '' 
        self.project_manager = '' 
        self.publisher = ''
        self.published_date = ''
        self.source_url = ''
        self.id = ''



def url_split(url, index, option):
    return url.rsplit('/', index)[option]


def word_split(string, index):
    return string.rsplit('->', 1)[index]


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


def get_number(string):
    return re.findall(r'[\d.]+', string)[0]


def search_txt(el, tag, word):
    try:
        element = el(tag, text=re.compile(word))[0]
        text_content = get_txt(element).split(word)[1]
        return remove_space(text_content)
    except:
        return ""


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
        return "<" + match.group(1) + match.group(2) + "=" + "\"" + absolutePath + "\"" + match.group(4) + "\"" + ">"
    except:
        effect_link = old_link.rsplit('./', 1)[1]
        pre_count = len(re.findall(r".\/", old_link))
        absolutePath = url_split(origin_url, pre_count, 0) + '/' + effect_link
        print(absolutePath)
        return "<" + match.group(1) + match.group(2) + "=" + "\"" + absolutePath + "\"" + match.group(4) + "\"" + ">"


def update_links(fileContents):
    p = re.compile(r"<(.*?)(src|href)=\"(?!http)((?!javascript).*?)\"(.*?)>")
    return p.sub(srcrepl, fileContents)


def get_download_link(origin_url, link):
    p = re.compile(r"^http|^javascript")
    if p.findall(link):
        return False
    else:
        match = re.search(r'(.\/)*([..\/]+)([\w.*]+)', link)
        if match:
            prefix_count = len(match.group(2).split('../'))
            file_name = match.group(3)
            file_url = origin_url.rsplit(
                "/", prefix_count)[0] + '/' + file_name
            return file_url
        else:
            return False


def add_console(text):
    print("\n********************************")
    print(text)
    print("********************************\n")



def get_links(url, page_num=1):
    global error_count
    origin_url = url_split(url, 1, 0)
    from_time = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    to_time = datetime.now().strftime('%Y-%m-%d')

    try:
        page_url = url + '&operateDateFrom='+ str(from_time) +'&operateDateTo='+ str(to_time) + '&pageIndex='+ str(page_num)
        response = post(page_url, headers=headers)
        sleep(2)

        elapsed_time = time() - start_time
        print('{} th request-> Frequency: {}'.format(page_num, elapsed_time))

        # Throw a warning for non-200 status codes
        if response.status_code != 200:
            warn('Request: {}; Status code: 200'.format(elapsed_time))

        try:
            page_html = BeautifulSoup(response.text, 'html.parser')
            links_container = page_html.select('.m_m_c_list li')

            # For every link of in a single page
            linkList = []
            next_page_flag = False

            for container in links_container:
                link_title = get_txt(container.find('a'))
                link_url = get_param(container.select_one('a[href*=html]'), 'href')
                link_date = get_txt(container.find('em')).split(' ')[0]
                legion_container = container.select('a[href*=javascript]')
                link_region = ''
                print(len(legion_container))
                if (legion_container  and len(legion_container) > 1) :
                    for item in legion_container:
                        link_region += ' ' + get_txt(item)

                abs_url = origin_url + link_url


                link = {
                    "title": link_title,
                    "date": link_date,
                    "region": link_region,
                    "url": abs_url
                }

                # Check if it is the part of last action
                error_count = 0
                next_page_flag = utils.get_item_exist(log_status, link)

                if not next_page_flag:
                    break
                else:
                    print("-> New One:  ", link_date)
                    linkList.append(links(link_title, abs_url, link_date, link_region))
        
            if next_page_flag == True:
                page_num += 1
                sleep(5)
                linkList += get_links(url, page_num)

            return linkList
        except Exception as e:
            print("Page contents Error", e)
    except ConnectionError as e:
        error_count +=1
        if error_count > 3:
            print("An exception occurred, We will reprocess this action 1 hour later!", e)
            sleep(3600)
        else:
            print("Request again!")
            sleep(1)
        get_links(url, page_num)



def get_contract(url, region=''):
    global error_count
    # Make a get request
    print("URL ====>", url)
    try:
        response = get(url, headers=headers)
        sleep(1)
        elapsed_time = time() - start_time
        print('Request-> Frequency: {}'.format(elapsed_time))

        # Throw a warning for non-200 status codes
        if response.status_code != 200:
            warn('Request: {}; Status code: 200'.format(elapsed_time))

        # Parse the content of the request with BeautifulSoup
        page_html = BeautifulSoup(response.text, 'html.parser')
        try:
            contract = Contracts()
            # Select all the link containers from a single page
            pageBody = page_html.select_one('.zw_c_c_cont')

            contract.source_url = url
            contract.id = url.rsplit("/", 1)[1].split(".")[0]
            contract.region = region
            contract.title = get_txt(page_html.select_one('.zw_c_c_title'))

            container = page_html.select_one('.zw_c_c_qx')
            contract.source = search_txt(container, 'span', '信息来源：')
            contract.publisher = search_txt(container, 'span', '发布机构：')
            contract.published_date = search_txt(container, 'span', '发布日期：')
            contract.procurement_number = get_txt(container.select_one('span>a'))
            contract.item_name = search_txt(container, 'span', '采购品目：')
            contract.deal_price = search_txt(container, 'span', '预算金额：')
            contract.agency = search_txt(container, 'span', '代理机构：')
            contract.responsible_person = search_txt(container, 'span', '项目负责人：')
            contract.project_manager = search_txt(container, 'span', '项目经办人：')


            contract_arry = []
            for key, value in contract.__dict__.items():
                contract_arry.append(value)

            sleep(3)
            all_links = [get_download_link(url, link['href']) for link in page_html.select(
                'p>a[href]') if get_download_link(url, link['href'])]

            error_count = 0

            return {
                "contract_detail": contract,
                "file_links": [],
                "page_content": response.text,
                "page_body": pageBody.prettify()
            }

        except Exception as e:
            print("Page contents Error", e)
            return False

    except:
        error_count +=1
        if error_count >3 :
            print('Frequency Request Error, Will handle this an hour later!')
            sleep(3600)
        else:
            print('Retry again!')
            sleep(1)
        get_contract(url)
        return False


def main():
    log_content = utils.get_log(base_urls)

    try:
        for target in base_urls:
            # Get CSV file path and File Prefix
            csv_file_name = target["category"] + ".csv"
            csv_file_path = CSV_PATH + target["level"] + "/" + csv_file_name
            folder_prefix = FILE_PATH + target["level"] + "/" + target["category"]
            processingId = target["level"] + "->" + target["category"]
            
            # Get log content to check what is a last action
            global log_status
            logIndex = next((i for i, item in enumerate(log_content) if item["category"] == target["category"] and item["level"] == target["level"]), -1)
            log_status = log_content[logIndex]

            # Get all contract links based on category
            add_console("Grabbing new links for " + processingId)
            new_links = get_links(target["url"])
        

            # Update log with current action info when there are new updates
            if len(new_links) > 0:
                add_console("Updating log for " + processingId)
                log_content[logIndex]["date"] = new_links[0].date
                log_content[logIndex]["url"] = new_links[0].url
                log_content[logIndex]["title"] = new_links[0].title

                # Update log file
                utils.write_log(log_content)
                add_console("Starting to grab contract for " + processingId)
            else:
                add_console("There is no new contracts in " + processingId)


            # # Get contract details, Download attached files, Save html contents, and Add it to CSV 
            for link in new_links:
                # Get sub folder name (use the contract url) 
                deal_folder_dir = url_split(link.url, 1, 1).rsplit('.')[0]
                folder_path = folder_prefix + "/" + deal_folder_dir

                # Grab contract details
                contract =  get_contract(link.url, link.region)

                # Download files and save contents
                if contract:
                    utils.download_html(folder_path, link.url, contract["page_body"])
                    utils.download_files(folder_path, contract["file_links"])
                    # utils.html2pdf(folder_path, link.url, contract["page_body"])
                    utils.append_new_row(csv_file_path, contract["contract_detail"], field_names["all"])

            add_console("File Upload: " + csv_file_path)
            utils.upload_objects(csv_file_path)
    
    except Exception as e:
        print("error", e)



_ = system('clear') 
# Time Schdule 
schedule.every().tuesday.at("18:00").do(main)
schedule.every().friday.at("18:00").do(main)

while True:
    schedule.run_pending()
    sleep(10)

# Quick TEST
# main()







