---
name: azure-pricing-bom
description: Build consultant-grade Azure cost estimates - a Low/High (or per-environment) BOM/BOQ Excel workbook with live formulas from Azure Retail Prices API list prices, cross-checked and shared as Azure Pricing Calculator links. Use whenever the user asks for a BOM, BOQ, bill of materials, pricing, cost estimate, budgetary estimate, run cost, TCO, VM lift pricing, PAYG vs reserved comparison, calculator link, or to check a team's pricing sheet for Azure. Also use for AWS/GCP estimates with the same workbook layout (API step differs).
---

# Azure pricing BOM

Deliverable = **one .xlsx** (authoritative) + **calculator share links** (one per scenario) + 3-line summary in chat. Word/deck only if asked.

## Steps

1. **Scope** - read the SOW/architecture/team sheet. List every billable component per environment, pick region (client's: Qatar Central, UAE North, Central India ...), decide scenarios: Low/High (presales) or per-env LZ/Dev/UAT/Prod (delivery) or PAYG/RI1/RI3 (VM lift). Low = planning minimum, High = ceiling. Default buffer 15 %. Note what is excluded (tax, EA discount, SIEM, licences the client already owns).
2. **Prices** - `scripts/price.py` against the Retail Prices API; never from memory. Examples:
   ```bash
   ~/.claude/skills/azure-pricing-bom/scripts/price.py --service "Virtual Machines" --region uaenorth --sku Standard_D4as_v5
   ~/.claude/skills/azure-pricing-bom/scripts/price.py --service "Virtual Machines" --region uaenorth --sku Standard_D4as_v5 --type Reservation
   ~/.claude/skills/azure-pricing-bom/scripts/price.py --service "Azure App Service" --region qatarcentral --product "Premium v3" --meter P1mv3
   ~/.claude/skills/azure-pricing-bom/scripts/price.py --service Storage --region uaenorth --product "General Block Blob v2" --meter "Hot ZRS Data Stored"
   ```
   Reservation meters are the full-term price (1 or 3 years): divide by 12 or 36 for monthly. Storage meters come tiered (`from N units`): first tier for <50 TB. If a SKU is missing in a region, say so and pick the nearest region/SKU explicitly. Check for retired SKUs (team sheets often carry them).
3. **Workbook** - write a spec JSON (shape: `reference/spec_example.json`) and run
   ```bash
   ~/.claude/skills/azure-pricing-bom/.venv/bin/python -I ~/.claude/skills/azure-pricing-bom/scripts/bom_xlsx.py spec.json ~/Downloads/<Client>_<Scope>_Azure-BOM_<yyyy-mm-dd>.xlsx
   ```
   Sheets: Summary (blocks, Low/High USD + local currency, buffer, calculator links) · Azure BOM (one line per meter, blue inputs, formulas) · Assumptions · Other licences · Sources. Per-env deliverable = one spec per env, one BOM sheet each (extend the script, keep the layout). Categories numbered "1. Edge, identity & API", "2. Application compute", "3. Data & storage", "4. AI & analytics", "5. Networking", "6. Security & monitoring", "7. Backup & DR".
   Recalc + check: `soffice --headless --convert-to xlsx --outdir calc <file>` then read with `data_only=True`; no `#REF!`/`#NAME?`, totals sane.
4. **Calculator** - open https://azure.microsoft.com/pricing/calculator/ in the built-in browser and build one estimate per scenario following `reference/calculator.md` (IndexedDB edit, reload, verify line totals against the sheet). Tolerance: VM-only to the cent; mixed PaaS within a few %, explain any gap (tiering, free grants, missing models).
5. **Share** - ask the user to sign in to the calculator in the browser pane, click Share → copy `https://azure.com/e/...` → Done, per estimate. Put links in Summary and in chat. Never enter credentials.
6. **Memory** - save a `<client>-bom` project memory: file path, totals, links, region, exclusions, corrections made to team sheets.

## Rules
- Excel is authoritative; calculator is the cross-check and excludes the buffer. Say so in Summary and chat.
- Hours per month 730, days 30.4, QAR 3.64 / AED 3.6725 per USD (pegs), INR state current rate with date.
- Zone redundancy in High always; Low can be single-zone but say it. No RA-GRS where the paired region is outside the country (Qatar).
- Private Link requires compatible tiers (Service Bus Premium, ACR Premium, APIM Standard v2+); flag team sheets that miss this.
- Keep xlsx lean: no per-service essays, one note column. Numbers in prose only when they change a decision.
- Copy the final xlsx to the user's deliverables folder; keep the generator spec next to it.

## Prior art
Patterns proven on real engagements: Low/High presales BOM with team-sheet corrections · per-environment BOM (LZ/Dev/UAT/Prod) with one calculator link each · 44-VM lift priced PAYG/RI1/RI3 matching the calculator to the cent · HPC/GPU BOQ with a utilisation model. If the user keeps project memories, check them for client-specific links and exclusions before starting.
