---
name: dgtw-grouping
description: Diagnose DGTW stock-characteristic group assignments and unclassifiable observations using the deterministic classifier.
---

# DGTW group diagnosis

Use after approved intake. The Python engine—not model judgment—assigns formation-year size, B/M and momentum groups using hierarchical 5×5×5 maxima and the selected B/M basis. Inspect `groups.json` for selected boundaries and reason codes. Review missing features, year joins, nonmonotone cutoffs, duplicated keys and unit mismatches; request source backfill only for the same security/date/metric. Do not copy group IDs from prior workbooks or fabricate values. Any source correction creates a new immutable run.

