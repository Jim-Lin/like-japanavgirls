# like-japanavgirls

## Structure
![structure](structure.png?raw=true)

## Preparement
1. register domain name with [お名前.com](http://www.onamae.com/)
1. Let's Encrypt certificate authority with [NGINX](https://github.com/Jim-Lin/like-japanavgirls/blob/master/etc/nginx/sites-available/default)
    - 80: web/
    - 5000: bot/server.py
    - 9090: api/main.go

## Facebook Messenger Bot with Python
### requisites
* requests
* beautifulsoup4
* boto3
* tornado
* pymongo

### face data (daily cron job)
- bot/scheduler.py: import ETL class from bot/etl.py to **fetch monthly, daily, and work face data**
    - ETL: import AWS class from bot/aws.py and DAO class from bot/dao.py
        - AWS: **insert_index_face for insert face data with index of ExternalImageId and search_faces for search faces' similarity above 20%**
        - DAO: **mongodb find and update operation**

#### mongodb sample document
```json
{
    "_id" : ObjectId("5877d3f47b991c5356a45xxx"),
    "id" : "103xxx",
    "img" : "http://pics.dmm.co.jp/mono/actjpgs/xxx.jpg",
    "name" : "XXX",
    "works" : [ 
        "2wwkxxx",
        ...
    ],
    "count" : 2,
    "like" : [ 
        "2017-03-13/17204117_xxx.jpg"
    ],
    "unlike" : [ 
        "2017-03-13/5_xxx.jpg"
    ]
}
```

### webhook
- bot/server.py: **launch webhook handler server for facebook app**
![webhook](images/bot/webhook.png?raw=true)

- bot/handler.py: post function for two type event
    - message: **text or attachments data**
    - postback: **user's feedback payload data to improve accuracy**

### facebook bot sample operation
- text
![text](images/bot/text.png?raw=true)

- attachment
![attachment](images/bot/attachment.png?raw=true)  
![result](images/bot/result.png?raw=true)

- feedback: if you think the second one is similar, press **O** button and send image again, and then you will get the new similarity order
![feedback](images/bot/feedback.png?raw=true)  
![new_result](images/bot/new_result.png?raw=true)



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
