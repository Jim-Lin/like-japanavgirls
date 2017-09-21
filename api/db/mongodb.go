package db

import (
	"github.com/magiconair/properties"
	"gopkg.in/mgo.v2"
	"gopkg.in/mgo.v2/bson"
	"path/filepath"
	"strconv"
	"time"
)

const (
	Host     = "localhost:27017"
	Database = "dark"
)

type Rank struct {
	Id    string
	Count int
}

var (
	Db *mgo.Database
)

func init() {
	abspath, _ := filepath.Abs("./")
	p := properties.MustLoadFile(abspath + "/db/mongodb.properties", properties.UTF8)

	info := &mgo.DialInfo{
		Addrs:    []string{Host},
		Database: Database,
		Username: p.MustGetString("username"),
		Password: p.MustGetString("password"),
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

func UpsertOneWeekRank(id string) {
	year, week := time.Now().ISOWeek()
	update := bson.M{"$push": bson.M{"vote": id}}
	_, err := Db.C("rank").Upsert(bson.M{"week": strconv.Itoa(year) + strconv.Itoa(week)}, update)
	if err != nil {
		panic(err)
	}
}

func AggregateWeekRank() []Rank {
	year, week := time.Now().ISOWeek()
	lastWeek := strconv.Itoa(year) + strconv.Itoa(week - 1)
	pipeline := []bson.M{
		bson.M{"$match": bson.M{"week": lastWeek}},
    bson.M{"$unwind": "$vote"},
    bson.M{"$group": bson.M{"_id": "$vote", "count": bson.M{"$sum": 1}}},
		bson.M{"$sort": bson.M{"count": -1}},
		bson.M{"$limit": 5},
	}
	pipe := Db.C("rank").Pipe(pipeline)
	result := []bson.M{}
	err := pipe.All(&result)
	if err != nil {
		panic(err)
	}

	var rank []Rank
	for _, v := range result {
		rank = append(rank, Rank{Id: v["_id"].(string), Count: v["count"].(int)})
	}

	return rank
}
