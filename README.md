- Facebook Messenger Bot (private for tester account): https://m.me/like-japanavgirls
- Web App: http://like-av.xyz/
- Chrome Extension: https://chrome.google.com/webstore/detail/like-japanavgirls/ehhdbpobmjcndjibgblgnbgmhjmfmhae
- iOS App: https://itunes.apple.com/us/app/likegirl/id1262331185

## Structure
![structure](structure.png?raw=true)

## Preparement
1. register domain name with [お名前.com](http://www.onamae.com/)
1. Let's Encrypt certificate authority with [NGINX](https://github.com/Jim-Lin/like-japanavgirls/blob/master/etc/nginx/sites-available/default)
1. run docker mongodb service: `docker run -p 27017:27017 -v <mount_path>:/data/db -d mongo --auth`
1. create facebook page for messenger

## Facebook Messenger Bot with Python
### requisites
* requests
* beautifulsoup4
* boto3
* tornado
* pymongo

### face data (daily cron job)
fetch monthly, daily, and work face data
```bash
$ python bot/scheduler.py
```

two main class to process data
- AWS([bot/aws.py](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/aws.py)): aws rekognition api
    - [insert_index_face](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/aws.py#L16-L22): insert face data with index of ExternalImageId
    - [search_faces](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/aws.py#L24-L58): search faces' similarity above 20%
- DAO([bot/dao.py](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/dao.py)): mongodb find and update operation
    - [find_one_actress_by_id](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/dao.py#L40-L42)
    - [update_one_info_by_actress](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/dao.py#L36-L38)
    - [find_one_works_by_id](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/dao.py#L32-L34)
    - [update_one_works_by_id](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/dao.py#L28-L30)
    - [update_one_feedback_by_id](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/dao.py#L24-L26)

#### mongodb sample document
```json
{
    "_id": ObjectId("5877d3f47b991c5356a45xxx"),
    "id": "103xxx",
    "img": "http://pics.dmm.co.jp/mono/actjpgs/xxx.jpg",
    "name": "XXX",
    "works": [
        "2wwkxxx",
        ...
    ],
    "count": 2,
    "like": [
        "2017-03-13/17204117_xxx.jpg"
    ],
    "unlike": [
        "2017-03-13/5_xxx.jpg"
    ]
}
```

### webhook
launch webhook handler server for facebook app
```bash
$ python bot/server.py
```

go to your app https://developers.facebook.com/apps/xxx/webhooks/ setting and input your webhook url

<img src="images/bot/webhook.png" width="50%" height="50%">

---

modify your Verify Token and Page Access Token in [bot/handler.py#L15-L16](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/handler.py#L15-L16)
- Verify Token: the same as above what you set
- Page Access Token: page which you created for messenger permissions

there are two type events in bot/handler.py post function
- message: **text** or **attachments** data
- postback: user's feedback **payload** data to improve accuracy

### facebook bot sample operation
- message event(text): response text in [bot/handler.py#L40-L42](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/handler.py#L40-L42)

<img src="images/bot/text.png" width="50%" height="50%">

---

- message event(attachment): load image data and search faces in [bot/handler.py#L44-L73](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/handler.py#L44-L73) and then responses if the image has matches face

<img src="images/bot/attachment.png" width="50%" height="50%">

---
<img src="images/bot/result.png" width="50%" height="50%">

---

- postback event(payload): if you think the second one is more similar than first one, press **O** button and then responses the postback event with payload data in [bot/handler.py#L75-L87](https://github.com/Jim-Lin/like-japanavgirls/blob/master/bot/handler.py#L75-L87). upload the same image again and then you will get the new similarity order

<img src="images/bot/feedback.png" width="50%" height="50%">

---
<img src="images/bot/new_result.png" width="50%" height="50%">

---

## Back-end Api Server with Go
### requisites
* github.com/aws/aws-sdk-go
* github.com/aws/aws-sdk-go/aws/...
* github.com/aws/aws-sdk-go/service/...
* gopkg.in/mgo.v2

### upload handler([api/main.go#L35-L60](https://github.com/Jim-Lin/like-japanavgirls/blob/master/api/main.go#L35-L60))
1. call aws rekognition SearchFacesByImage api in [SearchFacesByImage](https://github.com/Jim-Lin/like-japanavgirls/blob/master/api/aws/rekognition.go#L20-L72) funtion to search faces' similarity above 20%
1. select top 2 similarity and find actress data by id in [FindOneActress](https://github.com/Jim-Lin/like-japanavgirls/blob/master/api/db/mongodb.go#L33-L40)
1. create [Payload](https://github.com/Jim-Lin/like-japanavgirls/blob/master/api/main.go#L20-L31) response json format

### feedback handler([api/main.go#L62-L89](https://github.com/Jim-Lin/like-japanavgirls/blob/master/api/main.go#L62-L89))
1. if the value of key "ox" is "like", call aws rekognition IndexFaces api in [InsertIndexFaceByImage](https://github.com/Jim-Lin/like-japanavgirls/blob/master/api/aws/rekognition.go#L74-L102) funtion to add the face with the index
1. update "like or unlike" of image with id in [UpsertOneFeedback](https://github.com/Jim-Lin/like-japanavgirls/blob/master/api/db/mongodb.go#L42-L48)

## Front-end with native JavaScript (no 3rd party library)
### upload([web/app.js#L165-L200](https://github.com/Jim-Lin/like-japanavgirls/blob/master/web/app.js#L165-L200))
- url: http://like-av.xyz/api/upload
- method: POST in XMLHttpRequest
- form-data: {upload: \<blob\>}

#### response sample json
```json
{
    "Count": 2,
    "Data" : [
        {
        	"Id": "102xxx",
        	"Img": "http://pics.dmm.co.jp/mono/actjpgs/xxx.jpg",
        	"Name": "xxx",
        	"Similarity": "99.98"
        },
        ...
    ],
    "File" : "2017-03-20/12274445_xxx.jpg"
}
```

<img src="images/web/result.png" width="50%" height="50%">

---

### feedback([web/app.js#L11-L33](https://github.com/Jim-Lin/like-japanavgirls/blob/master/web/app.js#L11-L33))
- url: http://like-av.xyz/api/feedback
- method: POST in XMLHttpRequest
- json-data: {id: \<id\>, ox: \<ox\>, file: \<filename\>}

## Chrome-Extension
### context menu
set up context menu tree at install time and only for image context in [chrome-extension/background.js](https://github.com/Jim-Lin/like-japanavgirls/blob/master/chrome-extension/background.js)

<img src="images/chrome/context_menu.png" width="50%" height="50%">

---
popup window, preview, and call upload api in [chrome-extension/info.js#L199-L200](https://github.com/Jim-Lin/like-japanavgirls/blob/master/chrome-extension/info.js#L199-L200) and then get json data to show result

<img src="images/chrome/result.png" width="50%" height="50%">

---
