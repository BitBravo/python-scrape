### Installation
**- Set up Pipenv on your machine**
```
pip install pipenv
```

**- Enable virtualenv using Pipenv**
```
pipenv shell
```

**- Install python libraries**
```
pipenv install
```

**- AWS S3 configuration**
Set AWS configuration in config.ini
```
[AWS]
ACCESS_KEY: your aws access key
SECRET_KEY: your aws secrted key
REGION: your aws regison
BUCKET: S3 Bucket name
```

### How to run.
```
$ cd project_root
$ python bot.py
```

### Properties
It will run this script twice in a week.
To change this schedule times, please config it in bot.py.

-> Tuesday 18:00
-> Friday 18:00


> ***If you want to test it quickly, please disable the Time Schedule Block and enable Quick Test blok in bot.py file.***

This is a Time Schedule Block.

````
<b># Time Schdule </b>
schedule.every().tuesday.at("18:00").do(main)
schedule.every().friday.at("18:00").do(main)

while True:
    schedule.run_pending()
    sleep(10)
````
<b>Quick Test Block.</b>
````
# Quick TEST
# main()
````