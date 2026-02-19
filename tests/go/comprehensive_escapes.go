package main

import (
	"context"
	"sync"
	"time"
)

// ============================================================================
// INTERFACE-BASED ESCAPES
// ============================================================================

type Worker interface {
	Work()
}

type LeakyWorker struct{}

func (w *LeakyWorker) Work() {
	go func() {
		time.Sleep(2 * time.Second)
	}()
}

func EscapeViaInterface(input string) string {
	var w Worker = &LeakyWorker{}
	w.Work() // Goroutine escapes through interface
	return "ok"
}

// ============================================================================
// CLOSURE & CAPTURE ESCAPES
// ============================================================================

func EscapeViaClosure(input string) string {
	closure := func() {
		go func() {
			time.Sleep(2 * time.Second)
		}()
	}
	closure() // Goroutine spawned in closure
	return "ok"
}

func EscapeViaHigherOrderFunc(input string) string {
	fn := func(callback func()) {
		callback()
	}

	fn(func() {
		go func() {
			time.Sleep(2 * time.Second)
		}()
	})
	return "ok"
}

func EscapeViaFunctionFactory(input string) string {
	factory := func() func() {
		return func() {
			go func() {
				time.Sleep(2 * time.Second)
			}()
		}
	}

	createFunc := factory()
	createFunc() // Goroutine created through factory
	return "ok"
}

// ============================================================================
// CHANNEL ESCAPE VARIANTS
// ============================================================================

func EscapeViaUnbufferedChannelWait(input string) string {
	ch := make(chan int)
	go func() {
		time.Sleep(2 * time.Second)
		ch <- 1 // Send happens after function returns
	}()
	// No one receives, goroutine hangs
	return "ok"
}

func EscapeViaBufferedChannelNoRecv(input string) string {
	ch := make(chan int, 1) // Buffered
	go func() {
		for i := 0; i < 10; i++ {
			ch <- i // Goroutine keeps sending, no one receives
			time.Sleep(100 * time.Millisecond)
		}
	}()
	return "ok"
}

func EscapeViaChannelSelect(input string) string {
	ch1 := make(chan int)
	ch2 := make(chan int)

	go func() {
		select {
		case ch1 <- 1:
			// Blocked, no receiver
		case ch2 <- 2:
			// Blocked, no receiver
		}
		// Goroutine hangs
	}()
	return "ok"
}

func EscapeViaChannelRangeWithoutClose(input string) string {
	results := make(chan int)

	go func() {
		for i := 0; i < 10; i++ {
			results <- i
			time.Sleep(100 * time.Millisecond)
		}
		// Never closes the channel
	}()

	// No one receiving, no close signal
	return "ok"
}

// ============================================================================
// WAITGROUP ESCAPES - Misuse patterns
// ============================================================================

func EscapeWaitGroupWithoutAdd(input string) string {
	wg := sync.WaitGroup{}

	go func() {
		// Forgot to Add()
		defer wg.Done() // Panic: Done called without Add
		time.Sleep(2 * time.Second)
	}()

	// Note: This will panic, but demonstrates escape attempt
	return "ok"
}

func EscapeWaitGroupPartialWait(input string) string {
	wg := sync.WaitGroup{}

	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			time.Sleep(2 * time.Second)
		}(i)
	}

	// Only wait for first goroutine
	time.Sleep(100 * time.Millisecond)
	return "ok" // Other 4 goroutines escape
}

func EscapeWaitGroupInLoop(input string) string {
	for batch := 0; batch < 3; batch++ {
		wg := sync.WaitGroup{}

		for i := 0; i < 5; i++ {
			wg.Add(1)
			go func(id int) {
				defer wg.Done()
				time.Sleep(2 * time.Second)
			}(i)
		}

		if batch == 0 {
			wg.Wait() // Only wait first batch
		}
		// Other batches escape
	}
	return "ok"
}

// ============================================================================
// CONTEXT CANCELLATION FAILURES
// ============================================================================

func EscapeIgnoringContext(input string) string {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		for {
			time.Sleep(100 * time.Millisecond)
			// Never checks ctx.Done()
		}
	}()

	return "ok" // Goroutine ignores context
}

func EscapeWithContextTimeout(input string) string {
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			case <-time.After(2 * time.Second):
				// Timeout longer than context, goroutine escapes
			}
		}
	}()

	return "ok"
}

// ============================================================================
// MUTEX & LOCK ESCAPES
// ============================================================================

var sharedMutex sync.Mutex
var sharedValue int

func EscapeViaDeadlock(input string) string {
	sharedMutex.Lock()

	go func() {
		time.Sleep(100 * time.Millisecond)
		sharedMutex.Lock() // Will deadlock - goroutine never proceeds
		sharedValue++
		sharedMutex.Unlock()
	}()

	time.Sleep(1000 * time.Millisecond)
	sharedMutex.Unlock() // Will cause panic due to goroutine lock
	return "ok"
}

func EscapeViaNestedLocks(input string) string {
	m1 := &sync.Mutex{}
	m2 := &sync.Mutex{}

	go func() {
		m1.Lock()
		time.Sleep(100 * time.Millisecond)
		m2.Lock() // Will deadlock
	}()

	go func() {
		m2.Lock()
		time.Sleep(100 * time.Millisecond)
		m1.Lock() // Circular lock dependency
	}()

	return "ok"
}

// ============================================================================
// PANIC & RECOVERY ESCAPES
// ============================================================================

func EscapeViaUnhandledPanic(input string) string {
	go func() {
		panic("unhandled panic in goroutine")
	}()

	time.Sleep(100 * time.Millisecond)
	return "ok" // Process continues but goroutine crashed
}

func EscapeViaRecoveryFailure(input string) string {
	go func() {
		defer func() {
			if r := recover(); r == nil {
				// Recovery code never reaches hanging goroutine
			}
		}()

		time.Sleep(2 * time.Second) // Long operation that might be escaped
	}()

	return "ok"
}

// ============================================================================
// DEFER ESCAPE PATTERNS
// ============================================================================

func EscapeViaDefer(input string) string {
	defer func() {
		go func() {
			time.Sleep(2 * time.Second)
		}()
	}()

	return "ok" // Deferred goroutine launched at exit
}

func EscapeInDeferredFunc(input string) string {
	f := func() {
		go func() {
			time.Sleep(2 * time.Second)
		}()
	}

	defer f()
	return "ok"
}

// ============================================================================
// POINTER & INDIRECTION ESCAPES
// ============================================================================

type GoroutineLauncher struct {
	work func()
}

func EscapeViaPointerIndirection(input string) string {
	launcher := &GoroutineLauncher{
		work: func() {
			time.Sleep(2 * time.Second)
		},
	}

	go launcher.work()
	return "ok"
}

func EscapeViaMethodPointer(input string) string {
	launcher := &GoroutineLauncher{
		work: func() {
			time.Sleep(2 * time.Second)
		},
	}

	fn := launcher.work
	go fn()
	return "ok"
}

// ============================================================================
// MULTIPLE ESCAPE PATHS
// ============================================================================

func EscapeViaMultipleGoroutines(input string) string {
	for i := 0; i < 10; i++ {
		go func(id int) {
			select {
			case <-time.After(2 * time.Second):
				// Timeout, no cleanup
			}
		}(i)
	}
	return "ok"
}

func EscapeViaNestedSpawning(input string, depth int) string {
	if depth > 0 {
		go EscapeViaNestedSpawning(input, depth-1)
	} else {
		go func() {
			time.Sleep(2 * time.Second)
		}()
	}
	return "ok"
}

// ============================================================================
// BROADCAST CHANNEL ESCAPES
// ============================================================================

func EscapeBroadcastChannel(input string) string {
	done := make(chan struct{})
	// Never close done

	for i := 0; i < 10; i++ {
		go func(id int) {
			<-done // Goroutines wait forever
		}(i)
	}

	return "ok" // Goroutines all stuck waiting
}

// ============================================================================
// PROPER PATTERNS - For comparison
// ============================================================================

func ProperlyWaitedGoroutine(input string) string {
	wg := sync.WaitGroup{}
	wg.Add(1)

	go func() {
		defer wg.Done()
		time.Sleep(100 * time.Millisecond)
	}()

	wg.Wait() // Properly waited
	return "ok"
}

func ProperContextCancellation(input string) string {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	wg := sync.WaitGroup{}
	wg.Add(1)

	go func() {
		defer wg.Done()
		for {
			select {
			case <-ctx.Done():
				return
			case <-time.After(100 * time.Millisecond):
				// Work
			}
		}
	}()

	time.Sleep(200 * time.Millisecond)
	cancel()
	wg.Wait() // Properly waited for cancellation
	return "ok"
}

func ProperChannelClose(input string) string {
	results := make(chan int, 5)
	wg := sync.WaitGroup{}
	wg.Add(1)

	go func() {
		defer wg.Done()
		for i := 0; i < 5; i++ {
			results <- i
		}
		close(results) // Properly close
	}()

	for val := range results {
		_ = val
	}

	wg.Wait()
	return "ok"
}

func ProperlyTimeoutGoroutine(input string) string {
	done := make(chan struct{})

	go func() {
		defer close(done)
		time.Sleep(100 * time.Millisecond)
	}()

	select {
	case <-done:
		return "ok" // Goroutine completed
	case <-time.After(500 * time.Millisecond):
		return "ok" // Timeout is safe here
	}
}

func ProperBroadcastClose(input string) string {
	done := make(chan struct{})
	wg := sync.WaitGroup{}

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			<-done // Wait for broadcast
		}(i)
	}

	time.Sleep(100 * time.Millisecond)
	close(done) // Broadcast stop to all
	wg.Wait()
	return "ok"
}
