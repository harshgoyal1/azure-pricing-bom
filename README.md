# azure-pricing-bom

A [Claude Code](https://claude.com/claude-code) skill that builds Azure cost estimates the way a presales architect delivers them:

- **Excel BOM/BOQ** with live formulas (Summary by block, Low/High scenarios, buffer, local currency, Assumptions, Other licences, Sources)
- **List prices from the Azure Retail Prices API**, never from memory
- **Azure Pricing Calculator estimates** built by editing the calculator's local IndexedDB state from the browser, verified line by line against the sheet, then shared as `https://azure.com/e/...` links

## Install

```bash
git clone https://github.com/harshgoyal1/azure-pricing-bom ~/.claude/skills/azure-pricing-bom
cd ~/.claude/skills/azure-pricing-bom && python3 -m venv .venv && .venv/bin/pip install openpyxl
```

Then in Claude Code ask for a "BOM", "BOQ", "cost estimate" or "calculator link" for an Azure scope. The skill triggers on its own.

## Contents

| Path | What |
|---|---|
| `SKILL.md` | The method: scope → prices → workbook → calculator → share → notes, plus pricing rules |
| `scripts/price.py` | Retail Prices API lookup CLI (stdlib only). Handles pagination, reservation terms, storage tiers |
| `scripts/bom_xlsx.py` | JSON spec → formatted xlsx with formulas (`openpyxl`) |
| `reference/spec_example.json` | Spec shape for `bom_xlsx.py` |
| `reference/calculator.md` | Calculator automation recipes and known module field slugs for ~20 services |

## Quick try

```bash
scripts/price.py --service "Virtual Machines" --region uaenorth --sku Standard_D4as_v5
scripts/price.py --service "Virtual Machines" --region uaenorth --sku Standard_D4as_v5 --type Reservation
.venv/bin/python -I scripts/bom_xlsx.py reference/spec_example.json /tmp/example_bom.xlsx
```

## Notes

- Prices are Microsoft pay-as-you-go list prices in USD, excluding tax and negotiated discounts.
- The calculator links exclude the usage buffer and non-Azure licences; the workbook is the authoritative number.
- Calculator field slugs change over time. When a service is missing from `reference/calculator.md`, add it through the product picker, dump its `currentModuleState`, and extend the list.

MIT licence.
