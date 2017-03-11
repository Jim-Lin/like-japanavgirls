package main

import (
	"./aws"
	"./db"
	"encoding/json"
	"fmt"
	// "io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"
)

const (
	imagesRoot = "/var/www/like-av.xyz/images/"
)

type Payload struct {
	Count int
	File  string
	Data  []Face
}

type Face struct {
	Id         string
	Name       string
	Img        string
	Similarity string
}

func UploadHandler(w http.ResponseWriter, r *http.Request) {
	// allow cross domain AJAX requests
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")
	checkPost(w, r)

	err := r.ParseMultipartForm(32 << 20) // maxMemory
	checkNil(w, err)

	file, handler, err := r.FormFile("upload")
	checkNil(w, err)
	defer file.Close()

	b, err := ioutil.ReadAll(file)
	checkNil(w, err)

	js, err := searchFace(b, handler.Filename)
	checkNil(w, err)

	w.Write(js)
}

func FeedbackHandler(w http.ResponseWriter, r *http.Request) {
	// allow cross domain AJAX requests
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")
	checkPost(w, r)

	decoder := json.NewDecoder(r.Body)
	val := map[string]string{}
	err := decoder.Decode(&val)
	checkNil(w, err)

	fmt.Println(val)
	if val["ox"] == "like" {
		b, err := ioutil.ReadFile(imagesRoot + val["file"])
		checkNil(w, err)
		checkNil(w, aws.InsertIndexFaceByImage(val["id"], b))
	}

	db.UpsertOneFeedback(val["id"], val["ox"], val["file"])
}

func main() {
	http.HandleFunc("/upload", UploadHandler)     // set router
	http.HandleFunc("/feedback", FeedbackHandler) // set router
	err := http.ListenAndServe(":9090", nil)      // set listen port
	if err != nil {
		log.Fatal("ListenAndServe: ", err)
	}
}

func checkNil(w http.ResponseWriter, err error) {
	if err != nil {
		log.Println(err)
		// http.Error(w, err.Error(), http.StatusInternalServerError)
		// return

		responseEmptyPayload(w)
	}
}

func checkPost(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		log.Println("Allowed POST method only")
		// http.Error(w, "Allowed POST method only", http.StatusMethodNotAllowed)
		// return

		responseEmptyPayload(w)
	}
}

func responseEmptyPayload(w http.ResponseWriter) {
	emptyPayload := &Payload{
		Count: 0,
	}

	js, _ := json.Marshal(emptyPayload)
	w.Write(js)
}

func searchFace(b []byte, fileName string) ([]byte, error) {
	result, err := aws.SearchFacesByImage(b)
	if err != nil {
		return nil, err
	}

	emptyPayload := &Payload{
		Count: 0,
		File:  fileName,
	}

	if result == nil {
		js, err := json.Marshal(emptyPayload)
		if err != nil {
			return nil, err
		}

		return js, nil
	} else {
		today := time.Now().Local().Format("2006-01-02")
		fmt.Println(today)
		imageDir := imagesRoot + today
		os.Mkdir(imageDir, os.ModePerm)
		err := ioutil.WriteFile(imageDir+"/"+fileName, b, 0644)
		if err != nil {
			return nil, err
		}

		payload := &Payload{
			Count: 0,
			File:  today + "/" + fileName,
			Data:  []Face{},
		}

		for i := 0; i < 2 && i < len(*result); i++ {
			matchFace := (*result)[i]

			id := matchFace.Id
			similarity := strconv.FormatFloat(matchFace.Similarity, 'f', 2, 64)
			fmt.Println(id)
			fmt.Println(similarity)

			val := db.FindOneActress(id)
			fmt.Println(val)

			if len(val) == 0 {
				js, err := json.Marshal(emptyPayload)
				if err != nil {
					return nil, err
				}

				return js, nil
			}

			face := Face{
				Id:         id,
				Name:       val["name"],
				Img:        val["img"],
				Similarity: similarity,
			}

			payload.Count += 1
			payload.Data = append(payload.Data, face)
		}

		js, err := json.Marshal(payload)
		if err != nil {
			return nil, err
		}

		return js, nil
	}
}
