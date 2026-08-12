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

## CPI leg (Phase 4)

ARDL(p, q) in log differences on monthly inflation and Brent returns, selected on out-of-sample one-step forecast error. Run ids continue the append-only sequence. The Phase 3 VAR run count (5) is unchanged.

### Run 6

- Timestamp: 2026-08-12T06:36:27+00:00
- Spec hash: 0fc5004cc0409667731976d75361d8d0f1549bb0d665becbbb364f66467bdbab
- Out-of-sample metric: 1.712536
- BIC: n/a
- Diagnostics: Ljung-Box p=0.2372 (pass)
- Decision: kept
- Note: cpi-leg ARDL p=1 q=1 panel=monthly_panel_mean

### Run 7

- Timestamp: 2026-08-12T06:36:28+00:00
- Spec hash: f05ca55d8c7cd1a468ea38cb6ed8bb74532888c12996ca3103fdd806609a3500
- Out-of-sample metric: 1.701704
- BIC: n/a
- Diagnostics: Ljung-Box p=0.2666 (pass)
- Decision: kept
- Note: cpi-leg ARDL p=1 q=2 panel=monthly_panel_mean

### Run 8

- Timestamp: 2026-08-12T06:36:28+00:00
- Spec hash: daf49084ead9d1d5e1f4ea29167ab9ca507969cbb55f7b96717393b513ed3344
- Out-of-sample metric: 1.698463
- BIC: n/a
- Diagnostics: Ljung-Box p=0.2297 (pass)
- Decision: kept
- Note: cpi-leg ARDL p=1 q=3 panel=monthly_panel_mean

### Run 9

- Timestamp: 2026-08-12T06:36:28+00:00
- Spec hash: 0df55eb01516046843a6cc11e4c844ff6e323095a480b168d632fb81eed35107
- Out-of-sample metric: 1.745174
- BIC: n/a
- Diagnostics: Ljung-Box p=0.5646 (pass)
- Decision: discarded
- Note: cpi-leg ARDL p=2 q=1 panel=monthly_panel_mean

### Run 10

- Timestamp: 2026-08-12T06:36:28+00:00
- Spec hash: e93ec165f96d5fa9e5fcad9ea1f16546d3d64b319cfb3362bf69b417fc9ac3da
- Out-of-sample metric: 1.747116
- BIC: n/a
- Diagnostics: Ljung-Box p=0.5613 (pass)
- Decision: discarded
- Note: cpi-leg ARDL p=2 q=2 panel=monthly_panel_mean

### Run 11

- Timestamp: 2026-08-12T06:36:28+00:00
- Spec hash: ee64bad7fa8de83bebf947165d76e21dce02099023cc8c0a9860597073c566b8
- Out-of-sample metric: 1.752110
- BIC: n/a
- Diagnostics: Ljung-Box p=0.5858 (pass)
- Decision: discarded
- Note: cpi-leg ARDL p=2 q=3 panel=monthly_panel_mean
