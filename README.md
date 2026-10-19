# DU-AN-VIDEO-HUONG-DAN-CMP

This public source mirror contains the initial Python preflight and source-integrity gates, the portable start guide, and focused tests. Private handoff records and credentials are intentionally not included.

## Tests

```powershell
python -m pytest tests/ -q
python src/gates/quet_vo_rong.py
```

`kiem_dau_phien.py` is specific to the complete private workspace and requires local handoff records, a configured temporary directory, and the project's drive-space checks. It is not expected to pass in this source-only mirror.

Keep API keys, credentials, private keys, and local credential files out of version control. Store secrets outside the repository and rotate any credential that may have been exposed.
