# Offline analytical-report QA

- Inspect native-resolution crops before diagnosing small text in a long-page screenshot. Full-page downscaling can cause false illegibility judgments and incorrect OCR; reconcile with rendered font sizes and measured contrast.
- Exercise a self-contained report with the page network disabled. Bundle pinned runtime bytes and its license, and verify no external requests rather than assuming an inline-looking document is offline.
- Download exports into a fresh per-test directory and inspect the newly downloaded content. Reusing a previous CSV can turn a real export failure into a false passing test.
- Put completion feedback near its initiating control when a floating notification obscures report text. On narrow screens, compare the primary alternatives side by side and move a secondary baseline below rather than compressing all predictions into three columns.
- Record the tested artifact SHA256 alongside viewport and interaction evidence. Counts derived from repeated runs must preserve unique-case denominators; null costs and absent rule probabilities must remain unmeasured, not zero.
- On modern Node, native WebSocket can drive an already-authorized local CDP endpoint without installing Playwright. Create a dedicated tab; restore download policy and device/network overrides. Do not modify or close unrelated user tabs.
