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

    def search_faces(self, img_bytes):
        try:
            response = self.rekognition.search_faces_by_image(
                CollectionId = self.collection,
                Image = {'Bytes': img_bytes},
                MaxFaces = 20,
                FaceMatchThreshold = 0.5
            )
            print response

        except:
            response = {}

        if bool(response) and len(response["FaceMatches"]) != 0:
            similarity = response["FaceMatches"][0]["Similarity"]
            if similarity < 20:
                return

            external_image_id = response["FaceMatches"][0]["Face"]["ExternalImageId"]
            external_image_ids = [external_image_id]
            faces = [{"id": external_image_id, "similarity": similarity}]
            for i in xrange(1, len(response["FaceMatches"])):
                face = response["FaceMatches"][i]
                face_similarity = face["Similarity"]
                if face_similarity < 20:
                    return faces

                face_external_image_id = face["Face"]["ExternalImageId"]
                if face_external_image_id in external_image_ids:
                    continue

                external_image_ids.add(face_external_image_id)
                faces.add({"id": face_external_image_id, "similarity": face["Similarity"]})

            return faces
