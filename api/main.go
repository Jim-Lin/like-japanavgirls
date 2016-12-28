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
)

const (
	imagesRoot = "/var/www/like-av.xyz/images/"
)

type Payload struct {
	Id         string
	Name       string
	File       string
	Img        string
	Similarity string
}

func UploadHandler(w http.ResponseWriter, r *http.Request) {
	// allow cross domain AJAX requests
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")

	if r.Method != "POST" {
		http.Error(w, "Allowed POST method only", http.StatusMethodNotAllowed)
		return
	}

	err := r.ParseMultipartForm(32 << 20) // maxMemory
	if err != nil {
		log.Fatal(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	file, handler, err := r.FormFile("upload")
	if err != nil {
		log.Fatal(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer file.Close()

	b, err := ioutil.ReadAll(file)
	if err != nil {
		log.Fatal(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	js, err := searchFace(b, handler.Filename)
	if err != nil {
		log.Fatal(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Write(js)
}

func FeedbackHandler(w http.ResponseWriter, r *http.Request) {
	// allow cross domain AJAX requests
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")

	if r.Method != "POST" {
		http.Error(w, "Allowed POST method only", http.StatusMethodNotAllowed)
		return
	}

	decoder := json.NewDecoder(r.Body)
	val := map[string]string{}
	err := decoder.Decode(&val)
	if err != nil {
		log.Fatal(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}

	fmt.Println(val)
	db.UpsertOneFeedback(val["id"], val["ox"], val["image"])
}

func main() {
	http.HandleFunc("/upload", UploadHandler)     // set router
	http.HandleFunc("/feedback", FeedbackHandler) // set router
	err := http.ListenAndServe(":9090", nil)      // set listen port
	if err != nil {
		log.Fatal("ListenAndServe: ", err)
	}
}

func searchFace(b []byte, fileName string) ([]byte, error) {
	result, err := aws.SearchFacesByImage(b)
	if err != nil {
		return nil, err
	}

	emptyPayload := Payload{
		Id:   "",
		File: fileName,
	}

	if result == nil {
		js, err := json.Marshal(emptyPayload)
		if err != nil {
			return nil, err
		}

		return js, nil
	} else {
		id := result.Id
		similarity := strconv.FormatFloat(result.Similarity, 'f', 2, 64)
		fmt.Println(id)
		fmt.Println(similarity)

		os.Mkdir(imagesRoot+id, os.ModePerm)
		err := ioutil.WriteFile(imagesRoot+id+"/"+fileName, b, 0644)
		if err != nil {
			return nil, err
		}

		val := db.FindOneActress(id)
		fmt.Println(val)

		if len(val) == 0 {
			js, err := json.Marshal(emptyPayload)
			if err != nil {
				return nil, err
			}

			return js, nil
		}

		payload := Payload{
			Id:         id,
			Name:       val["name"],
			File:       fileName,
			Img:        val["img"],
			Similarity: similarity,
		}
		js, err := json.Marshal(payload)
		if err != nil {
			return nil, err
		}

		return js, nil
	}
}
