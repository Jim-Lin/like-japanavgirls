#!/usr/bin/python
# -*- coding: utf-8 -*-

import boto3
import urllib2
import re

class AWS:

    def __init__(self, *args, **kwargs):
        #args -- tuple of anonymous arguments
        #kwargs -- dictionary of named arguments
        self.bucket = "ranking-bucket"
        self.collection = "rankingcollection"

        self.rekognition = boto3.client('rekognition')
        self.s3 = boto3.client('s3')

    def insert_index_faces(self, actresses):
        for actress in actresses:
            print actress.get("img")

            pattern = re.compile("http://pics.dmm.co.jp/mono/actjpgs/medium/(.*)")
            match = pattern.search(actress.get("img"))
            img_name = match.group(1)

            try:
                self.s3.head_object(Bucket=self.bucket, Key=img_name)
            except:
                self.s3.upload_fileobj(urllib2.urlopen(actress.get("img")), self.bucket, img_name)

            response = self.rekognition.list_faces(CollectionId=self.collection)
            if not self.__contains_face(response.get("Faces"), lambda x: x.get("ExternalImageId") == actress.get("id")):
                response = self.rekognition.index_faces(
                    CollectionId = self.collection,
                    Image = {
                        'S3Object': {
                            'Bucket': self.bucket,
                            'Name': img_name
                        }
                    },
                    ExternalImageId = actress.get("id")
                )
                print response

    def search_face(self, img_bytes):
        response = self.rekognition.search_faces_by_image(
            CollectionId = self.collection,
            Image = {'Bytes': img_bytes},
            MaxFaces = 1,
            FaceMatchThreshold = 0.5
        )
        print response

        if len(response["FaceMatches"]) != 0:
            external_image_id = response["FaceMatches"][0]["Face"]["ExternalImageId"]
            similarity = response["FaceMatches"][0]["Similarity"]
            print external_image_id
            print similarity
            return {"id": external_image_id, "similarity": similarity}


    def __contains_face(self, list, filter):
        for x in list:
            if filter(x):
                return True
        return False
