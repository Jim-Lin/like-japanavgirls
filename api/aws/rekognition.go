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

func SearchFacesByImage(imgBytes []byte) (*Face, error) {
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
		MaxFaces:           aws.Int64(1),
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

	return &Face{*resp.FaceMatches[0].Face.ExternalImageId, *resp.FaceMatches[0].Similarity}, nil
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
