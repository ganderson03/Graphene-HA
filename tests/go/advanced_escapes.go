package escape_tests

import (
	"sync"
	"time"
)

// === Obfuscated Goroutine Escapes ===

func spawnViaFunction(_input string) string {
	fn := func() {
		func() {
			go func() {
				time.Sleep(2 * time.Second)
			}()
		}()
	}
	fn()
	return "ok"
}

func spawnViaMap(_input string) string {
	// Hide goroutine spawn in map value
	handlers := map[string]func(){
		"worker": func() {
			go func() {
				time.Sleep(2 * time.Second)
			}()
		},
	}
	handlers["worker"]()
	return "ok"
}

func spawnViaSlice(_input string) string {
	// Hide in slice
	tasks := []func(){
		func() {
			go func() {
				time.Sleep(2 * time.Second)
			}()
		},
	}
	for _, task := range tasks {
		task()
	}
	return "ok"
}

// === Delayed Escapes ===

var goroutineRegistry []*sync.WaitGroup

func SpawnToRegistry(_input string) string {
	wg := &sync.WaitGroup{}
	wg.Add(1)
	go func() {
		defer wg.Done()
		time.Sleep(2 * time.Second)
	}()
	goroutineRegistry = append(goroutineRegistry, wg)
	// Never wait for goroutine
	return "ok"
}

// === Conditional Escapes ===

func SpawnConditionalGoroutine(_input string) string {
	if len(_input) > 3 {
		go func() {
			time.Sleep(2 * time.Second)
		}()
	}
	return "ok"
}

func SpawnInErrorHandler(_input string) string {
	if _input == "trigger" {
		go func() {
			time.Sleep(2 * time.Second)
		}()
	}
	return "ok"
}

// === Dynamic Escapes ===

var goroutineMap = make(map[string]chan struct{})

func SpawnWithDynamicKey(_input string) string {
	key := "goroutine_" + _input
	ch := make(chan struct{})
	go func() {
		<-ch
		time.Sleep(2 * time.Second)
	}()
	goroutineMap[key] = ch
	// Never signal channel
	return "ok"
}

// === Goroutine Pool Escapes ===

type WorkerPool struct {
	workers []chan func()
}

func (p *WorkerPool) Submit(fn func()) {
	p.workers[0] <- fn
}

func LeakWorkerPool(_input string) string {
	pool := &WorkerPool{
		workers: []chan func(){make(chan func())},
	}

	// Start worker
	go func() {
		for fn := range pool.workers[0] {
			fn()
		}
	}()

	// Submit work but never close channel
	pool.Submit(func() {
		time.Sleep(2 * time.Second)
	})

	return "ok"
}

// === WaitGroup Issues ===

func WaitGroupPartialWait(_input string) string {
	wg := &sync.WaitGroup{}
	wg.Add(3)

	for i := 0; i < 3; i++ {
		go func() {
			defer wg.Done()
			time.Sleep(2 * time.Second)
		}()
	}

	// Only wait for 2 out of 3
	for i := 0; i < 2; i++ {
		wg.Wait()
	}

	return "ok"
}

func WaitGroupWithoutAdd(_input string) string {
	wg := &sync.WaitGroup{}
	// Forgot to call Add

	go func() {
		time.Sleep(2 * time.Second)
	}()

	wg.Wait()
	return "ok"
}

// === Channel Escapes ===

func LeakChannelWithoutClose(_input string) string {
	ch := make(chan struct{})
	go func() {
		<-ch
		time.Sleep(2 * time.Second)
	}()
	return "ok"
}

func LeakMultipleChannels(_input string) string {
	for i := 0; i < 3; i++ {
		ch := make(chan int)
		go func(c chan int) {
			x := <-c
			time.Sleep(time.Duration(x) * time.Second)
		}(ch)
		// Channels never sent to - goroutines block forever
	}
	return "ok"
}

// === Recursive Goroutines ===

func RecursiveGoroutines(_input string, depth int) string {
	if depth <= 0 {
		return "ok"
	}

	go func() {
		time.Sleep(100 * time.Millisecond)
		RecursiveGoroutines(_input, depth-1)
	}()

	return "ok"
}

// === Properly Cleaned Up (False Negatives) ===

func ProperlyJoinedGoroutine(_input string) string {
	done := make(chan struct{})
	go func() {
		defer close(done)
		time.Sleep(50 * time.Millisecond)
	}()
	<-done
	return "ok"
}

func ProperlyWaitedWaitGroup(_input string) string {
	wg := &sync.WaitGroup{}
	wg.Add(1)
	go func() {
		defer wg.Done()
		time.Sleep(50 * time.Millisecond)
	}()
	wg.Wait()
	return "ok"
}

func ProperlyClosedChannel(_input string) string {
	ch := make(chan struct{})
	go func() {
		<-ch
	}()
	close(ch)
	return "ok"
}
