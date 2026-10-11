# Rules for this repository

1. Never modify Superset source or build Superset's frontend. Only config, our pip packages, REST/ORM provisioning.
2. Never create anything in analytical databases. Superset uses the read-only role.
3. One calendar source: `nowruz.py`. Python, SQL and JS derive from it; parity tests guard it.
4. Filtering always on Gregorian columns; Jalali columns are for display and grouping.
5. Half-open ranges internally; inclusive Jalali dates in the UI.
6. Guest-token RLS carries security rules only, never user filters.
7. `DYNAMIC_PLUGINS` only together with the blueprint; the list endpoint must never return an error.
8. Plugin code: React 17 APIs only, no bundled React, no antd, no imports from Superset internals except via the shims.
9. Persian text: ی/ک (not ي/ك), ZWNJ where needed, RTL.
10. Every assumption about Superset internals gets a line in `docs/VERIFIED_FACTS.md` before code depends on it.
11. Secrets only via env; ship `.env.example`; no hard-coded hosts or IPs.
