package com.escape.tests.cases;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Task case 271: shadowed_sink_local_06 deep stress pattern. */
public class Case271ShadowedSinkLocal06 {
    private static final List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();
    private static final List<Supplier<String>> RETAINED_HANDLERS = new ArrayList<>();

    private interface Sink {
        void put(Map<String, String> obj);
    }

    private static void sink(Map<String, String> obj) {
        RETAINED_AUDIT.add(obj);
    }

    public static String execute(String input) {
        String taskName = "shadowed_sink_local_06";
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", taskName);
        payload.put("entity", "extreme");
        payload.put("stage", "stress");
        payload.put("input", raw);
        payload.put("checksum", taskName + ":" + raw.length());
        List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();
        RETAINED_AUDIT.add(payload);
        // SAFE: local shadow does not escape.
        return payload.get("checksum");
    }
}
