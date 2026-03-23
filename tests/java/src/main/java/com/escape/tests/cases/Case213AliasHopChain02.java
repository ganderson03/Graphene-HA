package com.escape.tests.cases;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Task case 213: alias_hop_chain_02 deep stress pattern. */
public class Case213AliasHopChain02 {
    private static final List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();
    private static final List<Supplier<String>> RETAINED_HANDLERS = new ArrayList<>();

    private interface Sink {
        void put(Map<String, String> obj);
    }

    private static void sink(Map<String, String> obj) {
        RETAINED_AUDIT.add(obj);
    }

    public static String execute(String input) {
        String taskName = "alias_hop_chain_02";
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", taskName);
        payload.put("entity", "extreme");
        payload.put("stage", "stress");
        payload.put("input", raw);
        payload.put("checksum", taskName + ":" + raw.length());
        Map<String, String> a = payload;
        Map<String, String> b = a;
        Map<String, String> c = b;
        // ESCAPE: multi-hop alias retained globally.
        RETAINED_AUDIT.add(c);
        return "ok";
    }
}
