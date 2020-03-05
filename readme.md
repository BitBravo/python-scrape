## Install Pipenv 
```
pip install pipenv
```
## Enable env

```
pipenv shell
pipenv install
```

## Please set AWS S3 configuration
<b>Please config it in config.ini</b>
```
[AWS]
ACCESS_KEY: your aws access key
SECRET_KEY: your aws secrted key
REGION: your aws regison
BUCKET: S3 Bucket name
```

## How to run this script.
```
$ cd project_root
python bot.py
```

## Properties
It will run this script twice in a week.
-> Tuesday 18:00
-> Friday 18:00


## Reference.
If you want to test it quickly, please disable the Time Schedule Block and enable Quick Test blok in bot.py file.

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