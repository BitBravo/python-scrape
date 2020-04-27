
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
                "date": (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d'),
                "title": None
            })
        return logs
        

def write_log(data):
    with open('log.json', 'w') as outfile:
        json.dump(data, outfile)