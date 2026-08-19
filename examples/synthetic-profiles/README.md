# Synthetic Profile Examples

These JSON files are reusable profiles for `init-city --synthetic-profile`.
They are deterministic testing fixtures, not calibrated census estimates.

Each file contains a `groups` array. A group sets a heritage or ethnic label,
its population share, optional income-band weights, and optional job-pool
weights.

Profiles can also include `mixed_households`. Each mixed household entry sets a
repeat `count`, a `members` list with per-person `heritage`, `income_band`, and
optional `age`, plus optional household-level `job_pools`.

Example:

```bash
PYTHONPATH=src python3 -m city_simulator init-city language-access-test \
  --synthetic \
  --people 120 \
  --synthetic-profile examples/synthetic-profiles/language-access-stress.json
```

Available profiles:

- `balanced-mixed-city.json`: broad income and job-pool mix for ordinary smoke
  tests.
- `language-access-stress.json`: residents with larger non-English language
  needs for service-access and interpreter-capacity tests.
- `income-polarization.json`: stronger high/low income separation for housing,
  budget, labor, and service-pressure tests.
