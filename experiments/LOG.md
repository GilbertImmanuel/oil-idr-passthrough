# Run log

## Format

Append-only. Add each run at the bottom. Do not edit or delete a recorded run. One entry per run,
including discarded runs. Each entry records:

- Run id: monotonic integer, starting at 1.
- Timestamp: ISO 8601 with timezone.
- Spec hash: sha256 of `experiments/spec.py` at run time.
- Out-of-sample metric: one-step forecast error on the held-out final 20 percent.
- BIC: on the training portion.
- Diagnostics: pass or fail for Ljung-Box, normality, and companion-matrix stability.
- Decision: kept or discarded.
- Note: one line on what changed relative to the previous run.

## Entries

No runs recorded yet.

### Run 1

- Timestamp: 2026-08-11T07:40:19+00:00
- Spec hash: 5a780be460a4a67d11f21040b97dda138957f3979adbb18b29b0cd7f6de043ad
- Out-of-sample metric: 1.101540
- BIC: -36.8142
- Diagnostics: Ljung-Box p=0.0000, normality p=0.0000, companion min modulus=4.7015 (fail)
- Decision: discarded
- Note: vars=4 lag=1 window=2019-01-01:2026-12-31

### Run 2

- Timestamp: 2026-08-11T07:40:21+00:00
- Spec hash: f03cf2fe3086cd05921c3745962bf18229081d1325354509852a5d99cc940af2
- Out-of-sample metric: 1.098680
- BIC: -36.7941
- Diagnostics: Ljung-Box p=0.0000, normality p=0.0000, companion min modulus=2.4172 (fail)
- Decision: discarded
- Note: vars=4 lag=2 window=2019-01-01:2026-12-31

### Run 3

- Timestamp: 2026-08-11T07:40:23+00:00
- Spec hash: c9e6027227a4d04066ab343403840e94d1d38175e2ebb3c08fab09a7921ebd6e
- Out-of-sample metric: 1.101193
- BIC: -36.7650
- Diagnostics: Ljung-Box p=0.0000, normality p=0.0000, companion min modulus=1.7466 (fail)
- Decision: discarded
- Note: vars=4 lag=3 window=2019-01-01:2026-12-31

### Run 4

- Timestamp: 2026-08-11T07:40:25+00:00
- Spec hash: 9dea7259eebd9f106868933c2ec291adf40af55699265883463d94c4044cc0de
- Out-of-sample metric: 1.105020
- BIC: -36.7083
- Diagnostics: Ljung-Box p=0.0000, normality p=0.0000, companion min modulus=1.5319 (fail)
- Decision: discarded
- Note: vars=4 lag=4 window=2019-01-01:2026-12-31

### Run 5

- Timestamp: 2026-08-11T07:40:27+00:00
- Spec hash: 39d44c7cbfde655ba543b0042bb8c9327a7d29a56d1ea1ea18c259f46dd21cd0
- Out-of-sample metric: 1.108315
- BIC: -36.6470
- Diagnostics: Ljung-Box p=0.0000, normality p=0.0000, companion min modulus=1.6063 (fail)
- Decision: discarded
- Note: vars=4 lag=5 window=2019-01-01:2026-12-31
