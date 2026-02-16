package escape_tests

import "time"

func SpawnDetachedGoroutine(_input string) string {
	go func() {
		time.Sleep(2 * time.Second)
	}()
	return "ok"
}

func SpawnWaitingGoroutine(_input string) string {
	block := make(chan struct{})
	go func() {
		<-block
	}()
	return "ok"
}
