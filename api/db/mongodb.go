package db

import (
	"gopkg.in/mgo.v2"
	"gopkg.in/mgo.v2/bson"
)

const (
	Host     = "localhost:27017"
	Database = "dark"
)

var (
	Db *mgo.Database
)

func init() {
	info := &mgo.DialInfo{
		Addrs:    []string{Host},
		Database: Database,
		Username: <username>,
		Password: <password>,
	}

	session, err := mgo.DialWithInfo(info)
	if err != nil {
		panic(err)
	}

	Db = session.DB(Database)
}

func FindOneActress(id string) map[string]string {
	result := map[string]string{}
	if err := Db.C("actress").Find(bson.M{"id": id}).Select(bson.M{"name": 1, "img": 1, "_id": 0}).One(&result); err != nil {
		panic(err)
	}

	return result
}

func UpsertOneFeedback(id string, ox string, image string) {
	update := bson.M{"$inc": bson.M{"count": 1}, "$push": bson.M{ox: image}}
	_, err := Db.C("actress").Upsert(bson.M{"id": id}, update)
	if err != nil {
		panic(err)
	}
}
