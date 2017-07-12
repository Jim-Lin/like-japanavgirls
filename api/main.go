package main

import (
	"./aws"
	"./db"
	"encoding/json"
	"fmt"
	"github.com/google/uuid"
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

var emptyPayload = Payload{Count: 0}

func UploadHandler(w http.ResponseWriter, r *http.Request) {
	defer func() { //catch or finally
		if err := recover(); err != nil { //catch
			log.Println(err)
			js, _ := json.Marshal(emptyPayload)
			w.Write(js)
		}
	}()

	// allow cross domain AJAX requests
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")
	checkPost(r)

	err := r.ParseMultipartForm(32 << 20) // maxMemory
	checkError(err)

	file, handler, err := r.FormFile("upload")
	checkError(err)
	defer file.Close()

	b, err := ioutil.ReadAll(file)
	checkError(err)

	w.Write(searchFace(b, handler.Filename))
}

func FeedbackHandler(w http.ResponseWriter, r *http.Request) {
	defer func() { //catch or finally
		if err := recover(); err != nil { //catch
			log.Println(err)
			js, _ := json.Marshal(emptyPayload)
			w.Write(js)
		}
	}()

	// allow cross domain AJAX requests
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")
	checkPost(r)

	decoder := json.NewDecoder(r.Body)
	val := map[string]string{}
	err := decoder.Decode(&val)
	checkError(err)

	fmt.Println(val)
	if val["ox"] == "like" {
		b, err := ioutil.ReadFile(imagesRoot + val["file"])
		checkError(err)
		checkError(aws.InsertIndexFaceByImage(val["id"], b))
	}

	db.UpsertOneFeedback(val["id"], val["ox"], val["file"])
	db.UpsertOneWeekRank(val["id"])
}

func main() {
	http.HandleFunc("/upload", UploadHandler)     // set router
	http.HandleFunc("/feedback", FeedbackHandler) // set router
	err := http.ListenAndServe(":9090", nil)      // set listen port
	if err != nil {
		log.Fatal("ListenAndServe: ", err)
	}
}

func checkError(err error) {
	if err != nil {
		// http.Error(w, err.Error(), http.StatusInternalServerError)
		// return
		panic(err)
	}
}

func checkPost(r *http.Request) {
	if r.Method != "POST" {
		// http.Error(w, "Allowed POST method only", http.StatusMethodNotAllowed)
		// return
		panic("Allowed POST method only")
	}
}

func searchFace(b []byte, fileName string) []byte {
	result, err := aws.SearchFacesByImage(b)
	if err != nil {
		panic(err)
	}

	if result == nil {
		js, err := json.Marshal(emptyPayload)
		if err != nil {
			panic(err)
		}

		return js
	} else {
		today := time.Now().Local().Format("2006-01-02")
		fmt.Println(today)
		imageDir := imagesRoot + today
		os.Mkdir(imageDir, os.ModePerm)
		uuidFileName := uuid.New().String()[:8] + "_" + fileName
		err := ioutil.WriteFile(imageDir + "/" + uuidFileName, b, 0644)
		if err != nil {
			panic(err)
		}

		payload := &Payload{
			Count: 0,
			File:  today + "/" + uuidFileName,
			Data:  []Face{},
		}

		for i := 0; i < 2 && i < len(result); i++ {
			var matchFace = result[i]

			id := (*matchFace).Id
			similarity := strconv.FormatFloat((*matchFace).Similarity, 'f', 2, 64)
			fmt.Println(id)
			fmt.Println(similarity)

			val := db.FindOneActress(id)
			fmt.Println(val)

			if len(val) == 0 {
				js, err := json.Marshal(emptyPayload)
				if err != nil {
					panic(err)
				}

				return js
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
			panic(err)
		}

		return js
	}
}
