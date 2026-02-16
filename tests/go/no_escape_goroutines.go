package escape_tests

import "time"

func JoinGoroutine(_input string) string {
	done := make(chan struct{})
	go func() {
		time.Sleep(10 * time.Millisecond)
		close(done)
	}()
	<-done
	return "ok"
}
