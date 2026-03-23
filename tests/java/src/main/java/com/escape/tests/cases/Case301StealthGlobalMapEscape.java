package com.escape.tests.cases;

import java.util.HashMap;
import java.util.Map;

/** Adversarial spoiler case 301: stealth global map escape. */
public class Case301StealthGlobalMapEscape {
    private static Map<String, Map<String, String>> sinkStore = new HashMap<>();

    public static String execute(String input) {
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", "stealth_global_map_escape");
        payload.put("entity", "spoiler");
        payload.put("stage", "adversarial");
        payload.put("input", raw);
        payload.put("checksum", "j301:" + raw.length());

        // ESCAPE: non-final static container with neutral naming.
        sinkStore.put("case301", payload);
        return "ok";
    }
}
