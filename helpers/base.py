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
    old_date = datetime.strptime(old["date"], '%Y-%m-%d')
    cur_date = datetime.strptime(item["date"], '%Y-%m-%d')

    if cur_date > old_date:
        return True
    elif cur_date == old_date:
        if not old["title"]:
            return True
        else:
            return old["title"] != item["title"]
    else:
        return False
