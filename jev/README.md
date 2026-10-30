# Jev experiment (parcels)

The scripts, pre-registered claims and saved answers behind the Jev numbers on the site. This repository holds the parcel half; the bin half is in the companion repository `bin-replenish-lab`. `REPORT.md` and `public_summary.md` cover both halves.

- `run_jev_parcels.py`: sends 150 synthetic test images (75 damaged, 75 clean) to the Jev service, two questions each (yes/no, then Box). Resumable.
- `analyse.py`: scores the saved answers against the claims in `claims.json`, writes `results/parcels.json` and `examples/`.
- `make_report.py`: writes `REPORT.md` and `public_summary.md` from `results/*.json`.
- `results/`: the saved answers (`raw_parcels.jsonl`), the call log and the summaries. They are the numbers on the site. (`bins.json` is the summary of the bin half, kept so the report builds.)
- `tests/`: offline tests with a stub transport. They make no network call and need no key.

## Running the real experiment costs money and sends images to a third party

It makes about 300 real calls to `api.typesafe.ai` (the full study was 456 calls, about 354,000 input tokens; the service reports tokens, not dollars). Set the key in the environment variable `JEV_API_KEY`; nothing else is read, and the key is never printed or stored. A hard cap of 700 calls is built in. The parcel images are regenerated first with `make results` in the repository root.

```sh
export JEV_API_KEY=...          # your own key
cd jev && python run_jev_parcels.py && python analyse.py && python make_report.py
```

Tests: `cd jev && python -m pytest tests`.

The experiment is marked experimental because TypeSafe marks image input and Box as experimental. Single run, one fixed prompt, nothing tuned.
