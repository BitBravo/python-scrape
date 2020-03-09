import boto3
import os
import csv
import json
import sys
import re
import subprocess
from xhtml2pdf import pisa
import configparser
from requests import get
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

s3_resource = boto3.resource("s3", region_name="us-east-1")

configParser = configparser.RawConfigParser()
configParser.read('config.ini')

ACCESS_KEY = configParser.get('AWS', 'ACCESS_KEY')
SECRET_KEY = configParser.get('AWS', 'SECRET_KEY')
REGION = configParser.get('AWS', 'REGION')
BUCKET = configParser.get('AWS', 'BUCKET')
FILE_PATH = configParser.get('LOCAL', 'FILE_DIR')
CSV_PATH = configParser.get('LOCAL', 'CSV_DIR')

s3_connect = boto3.client('s3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION
)


def file_validate(fpath):
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0

def get_last_date(fpath):
    try:
        csvfile = open(fpath, 'r')
        reader = csv.DictReader(csvfile, field_names)
        all_lines = list(reader)
        last_line = all_lines[-1]
        last_line_obj = json.loads(json.dumps(last_line))

        return last_line_obj["publish_date"]
    except:
        limit_time = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        return limit_time

def item_validate(fpath, title, date):
    with open(fpath, 'r') as fp:
        s = fp.read()
    if title in s and date in s:
        return False
    return False

def get_item_exist(old, item):
    old_date = datetime.strptime(old["date"],  '%Y-%m-%d')
    cur_date = datetime.strptime(item["date"],  '%Y-%m-%d')

    if cur_date > old_date:
        return True
    elif cur_date == old_date:
        if not old["title"]:
            return True
        else:
            return old["title"] != item["title"]
    else:
        return False

def append_new_row(csv_file_path, list_of_elem, field_names):
    create_folder(csv_file_path.rsplit("/", 1)[0])
    lineArray = []
    for field in field_names:
        lineArray.append(getattr(list_of_elem, field))

    with open(csv_file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_validate(csv_file_path):
            writer.writerow(field_names)
        writer.writerow(lineArray)
        f.close()


def create_folder(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
        print("Directory ", dir,  " Created ")
    else:
        print("Directory ", dir,  " already exists")


def download_files(deal_folder_dir, file_links):
    if len(file_links) > 0:
        create_folder(deal_folder_dir)

    for link in file_links:
        file_name = link.split('/')[-1]
        file_path = deal_folder_dir + '/' + file_name

        print("Started downloading file:%s" % file_name)
        # create response object
        r = get(link, stream=True)

        # download started
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)

        upload_objects(file_path)
        print("Finished downloading %s!\n" % file_name)

    return

def download_html(deal_folder_dir, url, content):
    file_name = url.split('/')[-1]
    file_path = deal_folder_dir + '/' + file_name
    create_folder(deal_folder_dir)

    print("Started downloading file:%s" % file_name)

    # download started
    with open(file_path, 'w') as f:
        f.write(content)

    upload_objects(file_path)
    print("Finished downloading! %s \n" % file_name)
    return

def html2pdf(deal_folder_dir, url, sourceHtml):
    file_name = url.split('/')[-1]
    file_name = re.sub(r'\.html?', '.pdf', file_name)

    file_path = deal_folder_dir + '/' + file_name
    create_folder(deal_folder_dir)

    contentData =  """<style>
                    @font-face {
                        font-family: 'DejaVu Sans';
                        src: url('./chinese.ttf');
                    }
                    html,body{
                        font-size: 12pt; 
                        font-family: 'DejaVu Sans'
                    }
              </style>
            """ + sourceHtml
    print("Started downloading file:%s" % file_name)

    try:
        resultFile = open(file_path, "w+b")
        pisaStatus = pisa.CreatePDF(contentData, resultFile)
        resultFile.close()
    except:
        if open and (not pisaStatus.err):
            if sys.platform == "win32":
                os.startfile(file_path)
            else:
                print(os)
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, file_path])

    return pisaStatus.err

def get_log(lists):
    try:
        with open('log.json') as json_file:
            return json.load(json_file)
    except:
        logs = []
        for item in lists:
            logs.append({
                "level": item["level"],
                "category": item["category"],
                 "url": None,
                "date": (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
                "title": None
            })
        return logs


def write_log(data):
    with open('log.json', 'w') as outfile:
        json.dump(data, outfile)

def upload_objects(file_name):
    try:
        s3_connect.upload_file(file_name, BUCKET, file_name)
    except ClientError as e:
        print(e)
