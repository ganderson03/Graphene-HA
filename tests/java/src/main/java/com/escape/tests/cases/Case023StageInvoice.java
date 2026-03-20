package com.escape.tests.cases;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Task case 023: stage invoice payload for downstream business processing. */
public class Case023StageInvoice {
    private static final Map<String, Map<String, String>> RETAINED_CACHE = new HashMap<>();
    private static final List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();
    private static final List<Supplier<String>> RETAINED_HANDLERS = new ArrayList<>();

    public static String execute(String input) {
        // Task: stage invoice records and prepare transport-ready payload.
        String taskName = "stage_invoice";
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", taskName);
        payload.put("entity", "invoice");
        payload.put("stage", "stage");
        payload.put("input", raw);
        // ESCAPE: closure captures payload and retained handler outlives function scope.
        Supplier<String> handler = () -> payload.get("task") + ":" + payload.get("input");
        RETAINED_HANDLERS.add(handler);
        return "ok";
    }
}
