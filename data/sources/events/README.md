# Hormuz event dates

Event list for the Phase 4 event study, at `hormuz_events.csv`. Committed because the
event study selects on these dates and a reader reproduces the abnormal-return result
only if the date list and its selection rule are fixed. Mirrors the provenance pattern
of `data/sources/cpi/`.

## Columns

- `date`: the incident date as reported. The event study maps each to t=0, the first
  trading day on or after the incident, against the daily panel.
- `description`: the incident.
- `source`: one named financial or wire report of the incident and its oil-price move.
- `retrieved`: retrieval date of the source, 2026-08-12.

## Selection rule

A date enters the list if, within the daily panel window 2019-01-03 to 2026-08-03, a
named financial or wire source reports a Hormuz-related oil supply-disruption event and
ties it to an oil-price move. Three inclusion classes:

1. An in-Strait or Strait-adjacent tanker attack or seizure.
2. An Iranian closure declaration or closure threat naming the Strait of Hormuz.
3. A Persian Gulf oil-infrastructure attack that the source prices as a Hormuz-region
   transit risk.

The event date is the incident date. The study maps it to t=0 as the first trading day
on or after the incident, so a weekend or holiday incident reacts on the next session.

## Excluded, with reason

- 2020-01-08 Iranian missile strikes on US bases in Iraq: the retaliation leg of the
  2020-01-03 Soleimani episode already listed. Excluded to avoid double-counting one
  episode.
- Red Sea and Bab-el-Mandeb Houthi shipping attacks, 2023 to 2024: a different
  chokepoint, not the Strait of Hormuz.
- OPEC production decisions and general Iran-Israel or Iran-US escalation not tied to
  Hormuz transit in the source.
- The 2026-08-06 Hormuz headlines in PROJECT_PLAN section 2 (Bloomberg and CNBC): dated
  after the daily panel end 2026-08-03, so they carry no post-event window in the data.
  They motivate the study and are excluded from the abnormal-return computation.

## Event count and power

Eleven events, all with t=0 and a five-trading-day post window inside the daily panel.
The count sits in the low teens, so the cross-event test carries low power (PROJECT_PLAN
section 10). The 2019 events (May, June, July, September) and the 2026 closure-episode
events (March to July) cluster, so their estimation and event windows overlap and the
events are not independent. The event study is reported as a supporting result, not the
headline (PROJECT_PLAN section 10).
