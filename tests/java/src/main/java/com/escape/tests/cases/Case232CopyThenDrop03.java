package com.escape.tests.cases;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Task case 232: copy_then_drop_03 deep stress pattern. */
public class Case232CopyThenDrop03 {
    private static final List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();
    private static final List<Supplier<String>> RETAINED_HANDLERS = new ArrayList<>();

    private interface Sink {
        void put(Map<String, String> obj);
    }

    private static void sink(Map<String, String> obj) {
        RETAINED_AUDIT.add(obj);
    }

    public static String execute(String input) {
        String taskName = "copy_then_drop_03";
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", taskName);
        payload.put("entity", "extreme");
        payload.put("stage", "stress");
        payload.put("input", raw);
        payload.put("checksum", taskName + ":" + raw.length());
        Map<String, String> copy = new HashMap<>(payload);
        copy.get("task");
        // SAFE: local copy not retained globally.
        return payload.get("checksum");
    }
}
