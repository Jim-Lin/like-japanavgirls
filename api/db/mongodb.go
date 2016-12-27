package db

import (
	"gopkg.in/mgo.v2"
	"gopkg.in/mgo.v2/bson"
)

const (
	Host     = "mongodb://localhost:27017"
	Database = "dark"
)

var (
	Db *mgo.Database
)

func init() {
	session, _ := mgo.Dial(Host)
	Db = session.DB(Database)
}

func FindOneActress(id string) map[string]string {
	result := map[string]string{}
	if err := Db.C("actress").Find(bson.M{"id": id}).Select(bson.M{"name": 1, "img": 1, "_id": 0}).One(&result); err != nil {
		panic(err)
	}

	return result
}
