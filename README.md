# giveradar

Python client and CLI for the [GiveRadar](https://giveradar.com) charity data API: 7.9 million+ nonprofits in 100+ countries, sourced from official government registries and tax authorities, with an integrity assessment, financials, leadership and red flags per organization.

```bash
pip install giveradar
```

Get a free API key at [giveradar.com/api/keys](https://giveradar.com/api/keys/) (10 requests/day; Pro 10,000/day) and set it once:

```bash
export GIVERADAR_API_KEY=gr_your_key
```

## Python

```python
from giveradar import Client

gr = Client()  # or Client(api_key="gr_...")

for c in gr.search("oxfam", country="GB")["results"]:
    print(c["name"], c["trust_score"], c["slug"])

charity = gr.charity("against-malaria-foundation")
print(charity["registration_number"], charity["annual_revenue"], charity["red_flags"])

gr.verify("1105319", country="GB")      # lookup by registration number or EIN
gr.financials("against-malaria-foundation")   # filings by year (Pro key)
gr.news("against-malaria-foundation")
gr.stats()
```

Every method returns the API's JSON as a dict. Errors are typed: `AuthenticationError`, `RateLimitError`, `NotFoundError`, `APIError`.

## CLI

```bash
giveradar search "red cross" --country US
giveradar verify 13-1644147 --country US
giveradar charity american-national-red-cross
giveradar financials american-national-red-cross
giveradar news american-national-red-cross
giveradar stats
```

Add `--json` to any command for raw output, `--key` to pass a key explicitly.

## For AI agents

GiveRadar also runs a free [MCP server](https://giveradar.com/mcp/). One line for Claude Code:

```bash
claude mcp add giveradar --transport http https://giveradar.com/mcp/
```

Setup for Claude Desktop, ChatGPT, Cursor and Gemini CLI: [giveradar.com/for-developers/#ai](https://giveradar.com/for-developers/#ai). Full machine-readable reference: [giveradar.com/llms-full.txt](https://giveradar.com/llms-full.txt).

## Links

- API documentation: https://giveradar.com/api/docs/
- OpenAPI specification: https://giveradar.com/api/openapi.yaml
- Plans and pricing: https://giveradar.com/api/
- Data sources by country: https://giveradar.com/data-sources/
- Methodology: https://giveradar.com/methodology/

## Licence

This client is MIT licensed. The data is free for individual use under the [GiveRadar Terms](https://giveradar.com/terms/); bulk and commercial access is licensed per contract (info@giveradar.com). Attribution requested: "GiveRadar (giveradar.com)".
