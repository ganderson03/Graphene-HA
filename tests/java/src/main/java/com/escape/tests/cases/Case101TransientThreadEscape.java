package com.escape.tests.cases;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

/**
 * Paper-inspired case 101: transient thread escape.
 * Motivated by schedule-sensitive runtime detection limits discussed in dynamic race diagnostics.
 */
public class Case101TransientThreadEscape {
    private static final List<Map<String, String>> RETAINED_CASE_101 = new ArrayList<>();

    public static String execute(String input) {
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", "transient_thread_escape");
        payload.put("entity", "thread");
        payload.put("stage", "deferred");
        payload.put("input", raw);

        // ESCAPE: payload escapes to worker thread that outlives function return briefly.
        Thread worker = new Thread(() -> {
            try {
                Thread.sleep(20);
            } catch (InterruptedException ignored) {
            }
            RETAINED_CASE_101.add(payload);
        });
        worker.start();

        return "queued";
    }
}
