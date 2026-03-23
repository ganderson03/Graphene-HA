package com.escape.tests.cases;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Task case 143: closure_chain_async_05 false-positive/false-negative stress pattern. */
public class Case143ClosureChainAsync05 {
    private static final Map<String, Map<String, String>> RETAINED_CACHE = new HashMap<>();
    private static final List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();
    private static final List<Supplier<String>> RETAINED_HANDLERS = new ArrayList<>();

    public static String execute(String input) {
        String taskName = "closure_chain_async_05";
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", taskName);
        payload.put("entity", "stress");
        payload.put("stage", "evaluation");
        payload.put("input", raw);
        payload.put("checksum", taskName + ":" + raw.length());
        Supplier<String> handler = () -> payload.get("input");
        // ESCAPE: retained closure captures payload.
        RETAINED_HANDLERS.add(handler);
        return "ok";
    }
}
