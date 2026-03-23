package com.escape.tests.cases;

import java.util.HashMap;
import java.util.Map;

/** Adversarial spoiler case 303: array-slot global escape. */
public class Case303ArraySlotEscape {
    private static Object[] slot = new Object[1];

    public static String execute(String input) {
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", "array_slot_escape");
        payload.put("entity", "spoiler");
        payload.put("stage", "adversarial");
        payload.put("input", raw);
        payload.put("checksum", "j303:" + raw.length());

        // ESCAPE: global object slot captures payload without retained-pattern names.
        slot[0] = payload;
        return "ok";
    }
}
