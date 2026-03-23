package com.escape.tests.cases;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Task case 188: local_cache_named_retained_09 false-positive/false-negative stress pattern. */
public class Case188LocalCacheNamedRetained09 {
    private static final Map<String, Map<String, String>> RETAINED_CACHE = new HashMap<>();
    private static final List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();
    private static final List<Supplier<String>> RETAINED_HANDLERS = new ArrayList<>();

    public static String execute(String input) {
        String taskName = "local_cache_named_retained_09";
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", taskName);
        payload.put("entity", "stress");
        payload.put("stage", "evaluation");
        payload.put("input", raw);
        payload.put("checksum", taskName + ":" + raw.length());
        Map<String, Map<String, String>> retainedLocal = new HashMap<>();
        retainedLocal.put("tmp", payload);
        // SAFE: local map does not escape.
        return payload.get("checksum");
    }
}
