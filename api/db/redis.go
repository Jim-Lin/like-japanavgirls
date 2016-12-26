package db

import (
	"fmt"
	"gopkg.in/redis.v5"
)

var client *redis.Client

func init() {
	client = redis.NewClient(&redis.Options{
		Addr: ":6379",
		DB:   0,
	})
	client.FlushDb()
}

func HGetAllByActressId(id string) map[string]string {
	val, err := client.HGetAll(id).Result()
	if err != nil {
		panic(err)
	}

	fmt.Println(val)
	return val
}
