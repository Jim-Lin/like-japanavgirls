package aws

import (
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/rekognition"
)

const (
	CollectionId = "rankingcollection"
	Region       = "us-east-1"
)

type Face struct {
	Id         string
	Similarity float64
}

func SearchFacesByImage(imgBytes []byte) ([]*Face, error) {
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String(Region),
	})
	if err != nil {
		fmt.Println("failed to create session,", err)
		return nil, err
	}

	svc := rekognition.New(sess)

	params := &rekognition.SearchFacesByImageInput{
		CollectionId:       aws.String(CollectionId), // Required
		Image:              &rekognition.Image{Bytes: imgBytes},
		FaceMatchThreshold: aws.Float64(0.2),
		MaxFaces:           aws.Int64(20),
	}
	resp, err := svc.SearchFacesByImage(params)

	if err != nil {
		// Print the error, cast err to awserr.Error to get the Code and
		// Message from an error.
		fmt.Println(err.Error())
		return nil, err
	}

	// Pretty-print the response data.
	fmt.Println(resp)

	if len(resp.FaceMatches) == 0 {
		fmt.Println("no match for face")
		return nil, nil
	}

	if *resp.FaceMatches[0].Similarity < 20 {
		fmt.Println("similarity less 20")
		return nil, nil
	}

	faces := []*Face{&Face{*resp.FaceMatches[0].Face.ExternalImageId, *resp.FaceMatches[0].Similarity}}
	ids := []string{*resp.FaceMatches[0].Face.ExternalImageId}
	for i := 1; i < len(resp.FaceMatches); i++ {
		face := resp.FaceMatches[i]
		if !hasElem(ids, *face.Face.ExternalImageId) {
			if *face.Similarity >= 20 {
				ids = append(ids, *face.Face.ExternalImageId)
				faces = append(faces, &Face{*face.Face.ExternalImageId, *face.Similarity})
			}
		}
	}

	return faces, nil
}

func InsertIndexFaceByImage(id string, imgBytes []byte) error {
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String(Region),
	})
	if err != nil {
		fmt.Println("failed to create session,", err)
		return err
	}

	svc := rekognition.New(sess)

	params := &rekognition.IndexFacesInput{
		CollectionId:    aws.String(CollectionId), // Required
		Image:           &rekognition.Image{Bytes: imgBytes},
		ExternalImageId: aws.String(id),
	}
	resp, err := svc.IndexFaces(params)

	if err != nil {
		// Print the error, cast err to awserr.Error to get the Code and
		// Message from an error.
		fmt.Println(err.Error())
		return err
	}

	// Pretty-print the response data.
	fmt.Println(resp)
	return nil
}

func hasElem(ids []string, id string) bool {
	set := make(map[string]bool)
	for _, v := range ids {
		set[v] = true
	}

	return set[id]
}
