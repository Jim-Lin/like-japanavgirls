#!/usr/bin/python
# -*- coding: utf-8 -*-

import boto3

class AWS:

    def __init__(self, *args, **kwargs):
        #args -- tuple of anonymous arguments
        #kwargs -- dictionary of named arguments
        self.bucket = "ranking-bucket"
        self.collection = "rankingcollection"

        self.rekognition = boto3.client('rekognition')

    def insert_index_face(self, actress_id, img_bytes):
        response = self.rekognition.index_faces(
            CollectionId = self.collection,
            Image = {'Bytes': img_bytes},
            ExternalImageId = actress_id
        )
        print response

    def search_face(self, img_bytes):
        try:
            response = self.rekognition.search_faces_by_image(
                CollectionId = self.collection,
                Image = {'Bytes': img_bytes},
                MaxFaces = 1,
                FaceMatchThreshold = 0.5
            )
            print response

        except:
            response = {}

        if bool(response) and len(response["FaceMatches"]) != 0:
            external_image_id = response["FaceMatches"][0]["Face"]["ExternalImageId"]
            similarity = response["FaceMatches"][0]["Similarity"]
            print external_image_id
            print similarity
            return {"id": external_image_id, "similarity": similarity}
