package com.escape.tests;

public class ThreadEscapes {
    public static String spawnNonDaemonThread(String input) {
        Thread thread = new Thread(() -> sleepMillis(2000), "escape-worker");
        thread.start();
        return "ok";
    }

    public static String spawnDaemonThread(String input) {
        Thread thread = new Thread(() -> sleepMillis(2000), "escape-daemon");
        thread.setDaemon(true);
        thread.start();
        return "ok";
    }

    public static String spawnMultipleThreads(String input) {
        for (int i = 0; i < 3; i++) {
            Thread thread = new Thread(() -> sleepMillis(2000), "escape-worker-" + i);
            thread.start();
        }
        return "ok";
    }

    public static String spawnWaitingThread(String input) {
        Object lock = new Object();
        Thread thread = new Thread(() -> {
            synchronized (lock) {
                try {
                    lock.wait();
                } catch (InterruptedException ignored) {
                }
            }
        }, "escape-waiter");
        thread.start();
        return "ok";
    }

    public static String joinThread(String input) {
        Thread thread = new Thread(() -> sleepMillis(50), "safe-worker");
        thread.start();
        try {
            thread.join();
        } catch (InterruptedException ignored) {
        }
        return "ok";
    }

    private static void sleepMillis(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException ignored) {
        }
    }
}
