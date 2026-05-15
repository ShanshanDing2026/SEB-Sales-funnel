# SEB-Sales-funnel
Tooling for sales funnel troubleshooting.

## Funnel troubleshooting tool

Use the CLI tool to identify the largest conversion drop and get targeted troubleshooting checks.

### Run

```bash
python3 funnel_troubleshooter.py --input ./funnel_metrics.json
```

Or use a URL as input:

```bash
python3 funnel_troubleshooter.py --input "https://example.com/funnel_metrics.json"
```

### Input format

```json
{
  "funnel_name": "SEB Sales Funnel",
  "stages": [
    {"name": "Landing", "count": 1200},
    {"name": "Signup", "count": 400},
    {"name": "Qualified", "count": 150},
    {"name": "Won", "count": 30}
  ]
}
```
