# like-japanavgirls

## Structure
![structure](structure.png?raw=true)

## Preparement
1. register domain name with [お名前.com](http://www.onamae.com/)
1. Let's Encrypt certificate authority with [NGINX](https://github.com/Jim-Lin/like-japanavgirls/blob/master/etc/nginx/sites-available/default)

## Facebook Messenger Bot with Python
### requisites
* requests
* beautifulsoup4
* boto3
* tornado
* pymongo

### collect face data (daily cron job)
- bot/scheduler.py import bot/etl.py to fetch data
    - bot/etl.py import bot/aws.py and bot/dao.py
        - aws.py: insert_index_face for insert face data to aws and search_faces for search similar face
        - dao.py: mongodb find and update operation


### webhook
bot/server.py launch webhook handler for facebook app
![webhook](images/bot/webhook.png?raw=true)


## Back-end Api Server with Go
### requisites
* github.com/aws/aws-sdk-go
* github.com/aws/aws-sdk-go/aws/...
* github.com/aws/aws-sdk-go/service/...
* gopkg.in/mgo.v2

## Front-end with native JavaScript
### request


## Chrome-Extension
https://chrome.google.com/webstore/detail/like-japanavgirls/ehhdbpobmjcndjibgblgnbgmhjmfmhae
