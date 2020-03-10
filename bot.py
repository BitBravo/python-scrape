from bs4 import BeautifulSoup
from requests import get
import re
import json
import configparser
from time import sleep, time
from random import randint
from warnings import warn
from collections import namedtuple
import utils
import schedule

configParser = configparser.RawConfigParser()
configParser.read('config.ini')
CSV_PATH = configParser.get('LOCAL', 'CSV_DIR')
FILE_PATH = configParser.get('LOCAL', 'FILE_DIR')
log_status = {}

base_urls = [
    { "level": "municipal", "category": "tender_notices", "url": "http://www.ccgp-beijing.gov.cn/xxgg/sjzfcggg/sjzbgg/index.html" },
    { "level": "municipal", "category": "deal_notices", "url": "http://www.ccgp-beijing.gov.cn/xxgg/sjzfcggg/sjzbjggg/index.html" },
    { "level": "municipal", "category": "contracts", "url": "http://www.ccgp-beijing.gov.cn/xxgg/sjzfcggg/sjhtgg/index.html" },
    { "level": "municipal", "category": "corrected_notices", "url": "http://www.ccgp-beijing.gov.cn/xxgg/sjzfcggg/sjgzgg/index.html" },
    { "level": "municipal", "category": "failed_notices", "url": "http://www.ccgp-beijing.gov.cn/xxgg/sjzfcggg/sjfbgg/index.html" },
    { "level": "municipal", "category": "single_source_notices", "url": "http://www.ccgp-beijing.gov.cn/xxgg/sjzfcggg/sjdygg/index.html" },
    { "level": "district", "category": "tender_notices", "url": "http://www.ccgp-beijing.gov.cn/xxgg/qjzfcggg/qjzbgg/index.html" },
    { "level": "district", "category": "deal_notices", "url": "http://www.ccgp-beijing.gov.cn/xxgg/qjzfcggg/qjzbjggg/index.html" },
    { "level": "district", "category": "contracts", "url": "http://www.ccgp-beijing.gov.cn/xxgg/qjzfcggg/qjhtgg/index.html" },
    { "level": "district", "category": "corrected_notices", "url": "http://www.ccgp-beijing.gov.cn/xxgg/qjzfcggg/qjgzgg/index.html" },
    { "level": "district", "category": "failed_notices", "url": "http://www.ccgp-beijing.gov.cn/xxgg/qjzfcggg/qjfbgg/index.html" },
    { "level": "district", "category": "single_source_notices", "url": "http://www.ccgp-beijing.gov.cn/xxgg/qjzfcggg/qjdygg/index.html" }
]

field_names = {
    "all": ['title', 'category', 'publish_date', 'contract_number', 'contract_name', 'serial_number', 'item_name', 'purchaser', 'supplier', 'region', 'price', 'signed_date', 'contract_publish_date', 'agency_name', 'deal_notice', 'appendix', 'source_url', 'id'],
    "sub": ['title', 'category', 'publish_date', 'source_url', 'id']
}

headers = {"Accept-Language": "en-US, en;q=0.5"}


# Preparing the monitoring of the loop
start_time = time()


class links:
    def __init__(self, title, url, date):
        self.title = title
        self.url = url
        self.date = date

class Contracts:
    def __init__(self):
        self.title = ''
        self.category = ''
        self.publish_date = ''
        self.contract_number = ''
        self.contract_name = ''
        self.serial_number = ''
        self.item_name = ''
        self.purchaser = ''
        self.supplier = ''
        self.region = ''
        self.price = ''
        self.signed_date = ''
        self.contract_publish_date = ''
        self.agency_name = ''
        self.deal_notice = ''
        self.appendix = ''
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

def get_links(url, page_num=0):
    origin_url = url_split(url, 1, 0)
    try:
        response = get(url, headers=headers)
        print(url)
        sleep(2)

        elapsed_time = time() - start_time
        print('Request-> Frequency: {}'.format(elapsed_time))

        # Throw a warning for non-200 status codes
        if response.status_code != 200:
            warn('Request: {}; Status code: 200'.format(elapsed_time))

        try:
            page_html = BeautifulSoup(response.text, 'html.parser')
            links_container = page_html.select('ul.xinxi_ul>li')

            # For every link of in a single page
            linkList = []
            next_page_flag = False
            for container in links_container:
                link_title = container.find('a').text
                link_url = container.find('a')['href']
                link_date = container.find('span').text
                abs_url = origin_url + '/' + link_url.rsplit("./", 1)[1]

                link = {
                    "title": link_title,
                    "date": link_date,
                    "url": abs_url
                }

                # Check if it is the part of last action
                next_page_flag = utils.get_item_exist(log_status, link)
                if not next_page_flag:
                    break
                else:
                    print("-> New One:  ", link_date)
                    linkList.append(links(link_title, abs_url, link_date))
        
            if next_page_flag == True:
                page_num += 1
                nextPage = origin_url + '/index_' + str(page_num) + '.html'
                sleep(5)
                linkList += get_links(nextPage, page_num)

            return linkList
        except Exception as e:
            print("Page contents Error", e)
    except:
        print("An exception occurred, We will reprocess this action 1 hour later!")
        sleep(3600)
        print('Request again')
        get_links(url, page_num)


def get_contract(url):
    # Make a get request
    print("URL ====>", url)
    response = get(url, headers=headers)
    sleep(1)
    elapsed_time = time() - start_time
    print('Request-> Frequency: {}'.format(elapsed_time))

    try:
        # Throw a warning for non-200 status codes
        if response.status_code != 200:
            warn('Request: {}; Status code: 200'.format(elapsed_time))

        # Parse the content of the request with BeautifulSoup
        page_html = BeautifulSoup(response.text, 'html.parser')
        try:
            contract = Contracts()
            # Select all the link containers from a single page
            contract.source_url = url
            contract.id = url.rsplit("/", 1)[1].split(".")[0]
            contract.title = get_txt(page_html.select_one(
                'div>span[style="font-size: 20px;font-weight: bold"]'))

            head_container = page_html.select_one('div.div_hui')
            category = get_txt(head_container.find('span', class_="zj_wz"))
            category_string = word_split(category, 1)
            contract.category = remove_space(category_string)
            contract.publish_date = get_txt(
                head_container.find('span', class_="datetime"))

            pageBody = page_html.select_one('div[style="width: 1105px;margin:0 auto"]')

            table_date = page_html.select('tr>td[colspan="3"]')

            if table_date:
                contract.contract_number = get_txt(table_date[0])
                contract.contract_name = get_txt(table_date[1])
                contract.serial_number = get_txt(table_date[2])
                contract.item_name = get_txt(table_date[3])
                contract.purchaser = get_txt(table_date[4])
                contract.supplier = get_txt(table_date[5])
                contract.region = get_txt(table_date[6])

                price_string = get_txt(table_date[7])
                contract.price = get_number(price_string)
                contract.signed_date = get_txt(table_date[8])
                contract.contract_publish_date = get_txt(table_date[9])
                contract.agency_name = get_txt(table_date[10])
                contract.deal_notice = get_txt(table_date[11].find('a'))
                contract.appendix = get_txt(page_html.select_one('p>a[href]'))

            # contract_arry = []
            # for _, value in contract.__dict__.items():
            #     contract_arry.append(value)

            sleep(3)
            all_links = [get_download_link(url, link['href']) for link in page_html.select(
                'p>a[href]') if get_download_link(url, link['href'])]

            return {
                "contract_detail": contract,
                "file_links": all_links,
                "page_content": response.text,
                "page_body": pageBody.prettify()
            }

        except Exception as e:
            print("Page contents Error", e)
            return False

    except:
        print('Frequency Request Error, Will handle this an hour later!')
        sleep(3600)
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
            new_links = get_links(target["url"], 0)
        

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


            # Get contract details, Download attached files, Save html contents, and Add it to CSV 
            for link in new_links:
                # Get sub folder name (use the contract url) 
                deal_folder_dir = url_split(link.url, 1, 1).rsplit('.')[0]
                folder_path = folder_prefix + "/" + deal_folder_dir

                # Grab contract details
                contract = get_contract(link.url)

                # Download files and save contents
                if contract:
                    if target["category"] == "contracts":
                        utils.download_html(folder_path, link.url, contract["page_content"])
                        utils.download_files(folder_path, contract["file_links"])
                        utils.append_new_row(csv_file_path, contract["contract_detail"], field_names["all"])
                    else:
                        utils.download_html(folder_path, link.url, contract["page_body"])
                        utils.download_files(folder_path, contract["file_links"])
                        # utils.html2pdf(folder_path, link.url, contract["page_body"])
                        utils.append_new_row(csv_file_path, contract["contract_detail"], field_names["sub"])

            add_console("File Upload: " + csv_file_path)
            utils.upload_objects(csv_file_path)
    
    except Exception as e:
        print("error", e)



# Time Schdule 
schedule.every().tuesday.at("18:00").do(main)
schedule.every().friday.at("18:00").do(main)

while True:
    schedule.run_pending()
    sleep(10)

# Quick TEST
main()

