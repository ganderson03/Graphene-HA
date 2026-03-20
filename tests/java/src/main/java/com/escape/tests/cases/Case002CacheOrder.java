package com.escape.tests.cases;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Task case 002: cache order payload for downstream business processing. */
public class Case002CacheOrder {
    private static final Map<String, Map<String, String>> RETAINED_CACHE = new HashMap<>();
    private static final List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();
    private static final List<Supplier<String>> RETAINED_HANDLERS = new ArrayList<>();

    public static String execute(String input) {
        // Task: cache order records and prepare transport-ready payload.
        String taskName = "cache_order";
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", taskName);
        payload.put("entity", "order");
        payload.put("stage", "cache");
        payload.put("input", raw);
        // ESCAPE: payload is copied into retained audit sink.
        RETAINED_AUDIT.add(payload);
        return "ok";
    }
}
