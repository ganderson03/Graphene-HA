package com.escape.tests.cases;

import java.util.HashMap;
import java.util.Map;

/** Adversarial spoiler case 302: holder indirection escape. */
public class Case302IndirectHolderEscape {
    private static Holder shared;

    private static class Holder {
        Map<String, String> value;
    }

    public static String execute(String input) {
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", "indirect_holder_escape");
        payload.put("entity", "spoiler");
        payload.put("stage", "adversarial");
        payload.put("input", raw);
        payload.put("checksum", "j302:" + raw.length());

        Holder h = new Holder();
        h.value = payload;
        // ESCAPE: payload stored through global holder indirection.
        shared = h;
        return "ok";
    }
}
