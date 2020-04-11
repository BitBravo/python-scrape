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
import utils
import inputs

configParser = configparser.RawConfigParser()
configParser.read('config.ini')
CSV_PATH = configParser.get('LOCAL', 'CSV_DIR')
FILE_PATH = configParser.get('LOCAL', 'FILE_DIR')
log_status = {}
error_count = 0

base_urls = inputs.base_urls
field_names = inputs.field_names

headers = {"Accept-Language": "en-US, en;q=0.5", "User-Agent":"Mozilla/5.0"}


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
        self.publisher = ''
        self.publish_date = ''
        self.item_name = ''
        self.procurement_number = ''
        self.contract_name = ''
        self.contract_number = ''
        self.deal_price = ''
        self.purchaser = ''
        self.supplier = ''
        self.contract_signed_date = ''
        self.appendix = ''
        self.source_url = ''
        self.id = ''



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
        reg = mathed +'(\s)?：([\u4e00-\u9fff\uff01-\uff150-9\s〔〕.*-a-zA-Z\(\)]+)<br/>'
        p = re.compile(reg)
        m = p.search(str(contents))
        return remove_space(m.groups()[1])
    except  Exception as e:
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


def get_download_link(origin_url, linkEl):
    try:
        fileLink = linkEl['href']
        fileName = get_txt(linkEl)

        p = re.compile(r"^http|^javascript")
        if p.findall(fileLink):
            return False
        else:
            match = re.search(r'(.\/)*([(\.\.\/)]*)([\w0-9\/.*?=&]+)', fileLink)
            if match:
                if not match.group(1) and not re.findall(match.group(2), '..'):
                    return [get_domain(origin_url) + '/' + match.group(3), fileName]
                else:
                    prefix_count = len(match.group(2).split('../'))
                    file_name = match.group(3)
                    file_url = origin_url.rsplit("/", prefix_count)[0] + '/' + file_name
                    return [file_url, fileName]
            else:
                return False
    except:
        return False


def add_console(text):
    print("\n********************************")
    print(text)
    print("********************************\n")



# Grab all contract links here
def get_links(url, page_num=1):
    global error_count
    linkList=[]

    origin_url = get_domain(url)
    page_url = url + '&page='+ str(page_num)

    print(page_url)

    try:
        response = post(page_url, headers=headers, timeout=10)
        sleep(3)

        elapsed_time = time() - start_time
        print('{} th request-> Frequency: {}'.format(page_num, elapsed_time))

        # Throw a warning for non-200 status codes
        if response.status_code != 200:
            warn('Request: {}; Status code: 200'.format(elapsed_time))

        page_html = BeautifulSoup(response.text, 'html.parser')
        links_container = page_html.select('.dataList li')

        # For every link of in a single page
        next_page_flag = False

        for container in links_container:
            link_title = get_txt(container.find('a'))
            link_url = get_param(container.find('a'), 'href')
            link_date = get_txt(container.select_one('span.time'))
           
            abs_url = origin_url + link_url


            link = {
                "title": link_title,
                "date": link_date,
                "url": abs_url
            }

            # Check if it is the part of last action
            error_count = 0
            next_page_flag = utils.get_item_exist(log_status, link)

            if not next_page_flag:
                break
            else:
                print("-> New One:  ", link_date, next_page_flag)
                linkList.append(links(link_title, abs_url, link_date))

        if next_page_flag == True:
            if len(linkList) != 0 or error_count > 10:
                page_num += 1
            else:
                error_count += 1

            sleep(3)
            linkList += get_links(url, page_num)

        return linkList
    except (Exception, ConnectionError, TimeoutError) as e:
        error_count +=1
        if error_count > 6:
            print("An exception occurred, We will reprocess this action 1 hour later!", e)
            sleep(3600)
        else:
            print("Request again!")
            sleep(2)

        linkList += get_links(url, page_num)
        return linkList
    

# Grab the contract detail here
def get_contract(url, category=''):
    global error_count
    # Make a get request
    print("URL ====>", url, category)
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
            pageBody = page_html.select_one('#pageContent table')

            contract.id = get_query(url, 'id')
            contract.source_url = url

            data_container = page_html.select_one("tbody div[style*='line-height']")
            contract.title = get_txt(data_container.select_one('font'))
            contract.category = get_txt(page_html.select('#crumbs a')[1])
            contract.publisher = get_txt(page_html.select("p[align='right']")[0])
            contract.publish_date = get_txt(page_html.select("p[align='right']")[1])
            
            if category == 'contract_notices':
                contract.item_name = get_search_str(data_container, '项目名称')
                contract.procurement_number = get_search_str(data_container, '项目编号')
                contract.contract_name = get_search_str(data_container, '合同名称')
                contract.contract_number = get_search_str(data_container, '合同编号')
                contract.deal_price = get_search_str(data_container, '合同金额\(万元\)')
                contract.purchaser = get_search_str(data_container, '采购单位')
                contract.supplier = get_search_str(data_container, '中标供应商')
                contract.contract_signed_date = get_search_str(data_container, '合同签订日期')
                contract.appendix = get_txt(data_container.select_one('a'))
                all_links = [get_download_link(url, link) for link in page_html.select('tbody a[href]') if get_download_link(url, link)]
            else:
                contract.appendix = get_txt(page_html.select_one('.line>a'))
                all_links = [get_download_link(url, link) for link in page_html.select('.line>a[href]') if get_download_link(url, link)]


            contract_arry = []
            for key, value in contract.__dict__.items():
                contract_arry.append(value)
            
            error_count = 0

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
        error_count +=1
        if error_count >3 :
            print('Frequency Request Error, Will handle this an hour later!')
            sleep(3600)
        else:
            print('Retry again!')
            sleep(1)
        get_contract(url)
        return False


# Main Process
def main():
    log_content = utils.get_log(base_urls)

    try:
        for target in base_urls:
            # Get CSV file path and File Prefix
            csv_file_name = target["category"] + ".csv"
            csv_file_path = 'results/' + CSV_PATH + target["level"] + "/" + csv_file_name
            folder_prefix = 'results/' + FILE_PATH + target["level"] + "/" + target["category"]
            processingId = target["level"] + "->" + target["category"]
            
            # Get log content to check what is a last action
            global log_status
            logIndex = next((i for i, item in enumerate(log_content) if item["category"] == target["category"] and item["level"] == target["level"]), -1)
            log_status = log_content[logIndex]

            # Get all contract links based on category
            add_console("Grabbing new links for " + processingId)
            new_links = get_links(target["url"])
           
            print('{} links found'.format(len(new_links)))


            # Update log with current action info when there are new updates
            if len(new_links) > 0:
                add_console("Updating log for " + processingId)
                log_content[logIndex]["date"] = new_links[0].date
                log_content[logIndex]["url"] = new_links[0].url
                log_content[logIndex]["title"] = new_links[0].title

                # Update log file
                utils.write_log(log_content)
                add_console("Starting to grab contract detail for " + processingId)
            else:
                add_console("There is no new contract in " + processingId)


            # Get contract details, Download attached files, Save html contents, and Add it to CSV 
            for link in new_links:
       
                # Get sub folder name (use the contract url)
                notice_id = get_query(link.url, 'id')
                folder_path = folder_prefix + "/" + notice_id

                # Grab contract details
                contract = get_contract(link.url, target["category"])

                # Download files and save contents
                if contract:
                    if target["category"] == "contract_notices":
                        utils.download_html(folder_path, link.url, contract["page_body"], notice_id)
                        utils.download_files(folder_path, contract["file_links"], notice_id)
                        utils.append_new_row(csv_file_path, contract["contract_detail"], field_names["all"])
                    else:
                        utils.download_html(folder_path, link.url, contract["page_body"], notice_id)
                        utils.download_files(folder_path, contract["file_links"], notice_id)
                        utils.append_new_row(csv_file_path, contract["contract_detail"], field_names["sub"])

            if len(new_links) > 0:
                add_console("File Upload: " + csv_file_path)
                utils.upload_objects(csv_file_path)
    
    except Exception as e:
        print("error", e)



_ = system('clear') 
# Time Schdule 
# schedule.every().tuesday.at("18:00").do(main)
# schedule.every().friday.at("18:00").do(main)

# while True:
#     schedule.run_pending()
#     sleep(10)


# Quick TEST
main()