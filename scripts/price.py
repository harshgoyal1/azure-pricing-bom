#!/usr/bin/env python3
"""Azure Retail Prices API lookup (stdlib only).

usage: price.py --service "Virtual Machines" --region uaenorth [--sku Standard_D4as_v5] [--meter "D4as v5"]
                [--product "Dasv5"] [--type Consumption|Reservation|DevTestConsumption] [--term "1 Year"] [--all]
Prints one line per meter: product | sku | meter | price unit | type/term. --json dumps raw items.
"""
import argparse, json, sys, urllib.parse, urllib.request

API = "https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&currencyCode=USD&$filter="

def fetch(flt):
    url, items = API + urllib.parse.quote(flt, safe="()',"), []
    while url:
        with urllib.request.urlopen(url, timeout=60) as r:
            d = json.load(r)
        items += d["Items"]; url = d.get("NextPageLink")
    return items

def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--service", required=True, help="serviceName, e.g. 'Virtual Machines', 'Azure App Service', 'Storage', 'SQL Database'")
    a.add_argument("--region", required=True, help="armRegionName: uaenorth, qatarcentral, centralindia, westeurope, Global ...")
    a.add_argument("--sku", help="armSkuName exact, e.g. Standard_D4as_v5")
    a.add_argument("--meter", help="meterName contains")
    a.add_argument("--product", help="productName contains")
    a.add_argument("--type", default="Consumption", help="priceType (default Consumption); use '' for all")
    a.add_argument("--term", help="reservationTerm: '1 Year' or '3 Years'")
    a.add_argument("--all", action="store_true", help="include Spot/Low Priority/Windows meters (hidden by default)")
    a.add_argument("--json", action="store_true")
    o = a.parse_args()
    f = [f"serviceName eq '{o.service}'", f"armRegionName eq '{o.region}'"]
    if o.sku: f.append(f"armSkuName eq '{o.sku}'")
    if o.type: f.append(f"priceType eq '{o.type}'")
    if o.term: f.append(f"reservationTerm eq '{o.term}'")
    if o.product: f.append(f"contains(productName, '{o.product}')")
    if o.meter: f.append(f"contains(meterName, '{o.meter}')")
    items = fetch(" and ".join(f))
    if not o.all:
        items = [i for i in items if not any(k in i["meterName"] for k in ("Spot", "Low Priority")) and "Windows" not in i["productName"]]
    if o.json:
        json.dump(items, sys.stdout, indent=1); return
    if not items:
        print("no meters. Loosen the filter (drop --sku, try --product/--meter) or check region slug.", file=sys.stderr); sys.exit(1)
    for i in sorted(items, key=lambda x: (x["productName"], x["meterName"], x.get("reservationTerm") or "")):
        tier = f' | from {i["tierMinimumUnits"]:g} units' if i.get("tierMinimumUnits") else ""
        term = f' {i["reservationTerm"]} (full-term price)' if i.get("reservationTerm") else ""
        print(f'{i["productName"]} | {i["armSkuName"]} | {i["meterName"]} | {i["unitPrice"]:g} per {i["unitOfMeasure"]} | {i["type"]}{term}{tier}')

if __name__ == "__main__":
    main()
