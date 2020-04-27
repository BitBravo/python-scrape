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
                          region_name=REGION)


def create_folder(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
        print("Directory ", dir, " Created ")
    else:
        print("Directory ", dir, " already exists")


def download_files(deal_folder_dir, file_links, file_name=False):
    if len(file_links) > 0:
        create_folder(deal_folder_dir)

    for link in file_links:
        ext = link[1].rsplit('.')[1]
        file_name = '{}.{}'.format(
            file_name, ext) if file_name else link[0].split('/')[-1]
        print('file ===>', file_name)
        file_path = deal_folder_dir + '/' + file_name

        print("Started downloading file:%s" % file_name)
        # create response object
        r = get(link[0], stream=True)

        # download started
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        upload_objects(file_path)
        print("Finished downloading %s!\n" % file_name)

    return


def download_html(deal_folder_dir, url, content, file_name=False):
    file_name = '{}.html'.format(file_name) if file_name else link.split(
        '/')[-1]
    print('file ===>', file_name)
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

    contentData = """<style>
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

    upload_objects(file_path)
    return pisaStatus.err


def upload_objects(file_name):
    print(file_name.split('/', 1)[1])
    try:
        s3_connect.upload_file(file_name, BUCKET, file_name.split('/', 1)[1])
    except ClientError as e:
        print(e)
