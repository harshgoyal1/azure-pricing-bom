# Azure Pricing Calculator automation (built-in browser)

URL: https://azure.microsoft.com/pricing/calculator/  State lives in IndexedDB `localforage` → object store `keyvaluepairs`:
- `azure_calculator_v3_estimates` : { [estimateId]: { id, estimateName, modules[], estimatePrice, saved } }
- `azure_calculator_v3_active_estimate_id` : id of the estimate on screen
Edit the JSON → `put` → `location.reload()` → app recalculates. **Every module edit goes through the store, not the UI.**

## Helpers (paste at top of every javascript_tool call; nothing persists across reloads except localStorage)
```js
const db=await new Promise(res=>{const r=indexedDB.open('localforage');r.onsuccess=()=>res(r.result)});
const get=k=>new Promise(res=>{const q=db.transaction('keyvaluepairs').objectStore('keyvaluepairs').get(k);q.onsuccess=()=>res(q.result)});
const put=(k,v)=>new Promise(res=>{const tx=db.transaction('keyvaluepairs','readwrite');tx.objectStore('keyvaluepairs').put(v,k);tx.oncomplete=()=>res()});
const est=await get('azure_calculator_v3_estimates'); const id=await get('azure_calculator_v3_active_estimate_id');
```

## 1. Add a product once via the picker (gets a correct module template)
```js
window.__add=async(name,titleRe)=>{const inp=document.querySelector('input[placeholder="Search products"]');
 Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(inp,name); inp.dispatchEvent(new Event('input',{bubbles:true}));
 await new Promise(r=>setTimeout(r,1500)); const bs=[...document.querySelectorAll('button[data-slug].pickerItem__button--add')];
 const b=bs.find(x=>new RegExp(titleRe||('^'+name+'$'),'i').test(x.title)); if(!b) return 'NOTFOUND '+bs.map(x=>x.title+'['+x.dataset.slug+']').join(' ; ');
 b.click(); await new Promise(r=>setTimeout(r,1500)); return 'added '+b.title+' ['+b.dataset.slug+']'};
await window.__add('Virtual Machines'); await window.__add('App Service'); await window.__add('Azure SQL Database','^Azure SQL Database$');
```
Then dump each module's editable fields to learn the slugs for this service:
```js
const skip=/Dropdown|Options|prices|layoutId|hasPricing|isBreakingChange|isCollapsed|shouldShow|version|isDeprecated|Remaining|description/;
est[id].modules.map((m,i)=>i+' '+m.serviceSlug+': '+JSON.stringify(Object.fromEntries(Object.entries(m.currentModuleState).filter(([k,v])=>!skip.test(k)&&(typeof v!=='object'||v===null))))).join('\n')
```
Allowed values for a dropdown: `document.getElementById(m.currentModuleState.layoutId).querySelectorAll('select')` → `[...sel.options].map(o=>o.value)`.

## 2. Clone a template module N times (VM lists, per-env copies)
```js
const T=est[id].modules.find(m=>m.serviceSlug==='virtual-machines');
const mk=(name,o)=>{const m=JSON.parse(JSON.stringify(T)); const s=m.currentModuleState; s.layoutId=m.serviceSlug+'-'+crypto.randomUUID()+'-layout';
 s.displayName=name; Object.assign(s,o); if('onSelectModuleId' in m) m.onSelectModuleId=s.layoutId; return m;};
est[id].modules=ROWS.map(([n,o],i)=>{const m=mk(n,o); m.index=i; return m;}); est[id].estimateName='Client - scenario';
await put('azure_calculator_v3_estimates',est); location.reload(); 'ok'
```
Always: new `layoutId` per module, sequential `index`, `onSelectModuleId = layoutId` when the key exists.

## 3. New estimate from an existing one (High from Low, RI from PAYG)
```js
const e=JSON.parse(JSON.stringify(est[id])); e.id=crypto.randomUUID(); e.saved=false; e.estimateName='... HIGH';
e.modules.forEach(m=>{const s=m.currentModuleState; s.layoutId=m.serviceSlug+'-'+crypto.randomUUID()+'-layout'; if('onSelectModuleId' in m) m.onSelectModuleId=s.layoutId;});
est[e.id]=e; await put('azure_calculator_v3_estimates',est); await put('azure_calculator_v3_active_estimate_id',e.id); location.reload(); e.id
```
Switch estimate on screen: `put('azure_calculator_v3_active_estimate_id', someId); location.reload()`. Park ids in `localStorage` (`__proj_ids`) so they survive reloads.

## 4. Verify after reload (wait 8–15 s; 40+ modules need 30 s, wait loops when pane hidden)
```js
await new Promise(r=>setTimeout(r,10000)); /* helpers */ const e=est[id];
({name:e.estimateName,total:Math.round(e.estimatePrice),rows:e.modules.map((m,i)=>i+' | '+m.currentModuleState.displayName.slice(0,60)+' | $'+Math.round(m.currentModuleState.total||0)+' | '+(m.currentModuleState.description||'').slice(0,120)).join('\n')})
```
`description` is the calculator's own text of what it priced: read it to confirm SKU/region/hours were accepted. A module with `total:0` and empty description usually has a wrong slug.
Compare per line against the xlsx; fix until the total matches (a pure VM estimate should match to the cent).

## 5. Share link (the user does the sign-in)
1. Tell the user: "Sign in to the calculator in the browser pane" (button top-right). Never type credentials.
2. Click **Share** (not Save), then in the dialog copy the `https://azure.com/e/<32 hex>` link, click **Done**.
3. Repeat per estimate (switch active id → reload → Share). Paste links into the Summary sheet and memory.
Opening a share link in any browser imports that estimate into local IndexedDB, so re-opening later works without sign-in.

## Known slugs / fields (collected Oct 2026)
- virtual-machines: `region:'uae-north'|'qatar-central'|'central-india'`, `operatingSystem:'linux'|'windows'`, `type:'os-only'`, `size:'d4asv5'|'d16alsv7'|'dc2sv3'|'d2alsv7'|'d8alsv7'`, `instances`, `hours`, `managedDisks`, `managedDiskRedundancy:'lrs'`, `managedDiskTier:'standardssd'|'premiumssd'`, `managedDiskType:'e4'..'e50'|'p10'...`, `computeBillingOption`+`billingOption:'payg'|'one-year'|'three-year'`, `interRegionUnits`, `internetEgressUnits`.
- app-service: `region, tier:'premiumv3', size:'p1mv3'|'p2mv3', type:'linux', instances`.
- azure-sql-database: `instanceSize` (vCores), `databaseBillingOption:'payg'`, `zoneRedundancy:'local'|...`, `singleStorageUnits`, `ltrDatabaseSize`; serverless: `duration` (vCore-seconds).
- front door: `tier:'frontdoorpremium'|'frontdoorstandard', zone:'zone7', internetEgressCount, inboundUnits, standardPremiumRequests`.
- storage (blob): `count` (GB), `blobWriteOperations`, `blobReadOperations`, `redundancy`.
- azure-openai: `modelForLanguage:'gpt5-2025-08-07'|'gpt5-nano'`, `prompt`, `completion` (thousands of tokens).
- api-management: `units`, `scaleOutUnits`; container-apps: `requestsInMillions, vCpuCount, memorySize, activeUsageExecutionMsPerRequest`; logic-apps: `standardPlan:'consumption', actionExecutions, actionDays`.
- cosmos-db: `databaseOperation:'serverless', userRequestUnits, userStorageUnits`; managed redis: `sizes:'b0'|'b5', instances`.
- defender: `planType:'workloadprotection', appServiceNodes, sqlDbServers, storageUnits, malwareScanning, keyVaults, azureResourceManager, defenderPlan:'p1'|'p2', aiTokens, postureMgmtNodes`.
- log analytics: `dailyLogsIngested, dataArchiveLogs, webTests`; private link: `privateEndpointUnits, inboundDataUnits, outboundDataUnits`; vnet: `vNet1Peering, vNet2Peering`; key vault: `operations, keys`.
- ai search: `units, queries`; document intelligence: `formRecognizerTier:'s0', formRecognizerFeature:'prebuilt', formRecognizerPagesPrebuiltTransactions`; translator: `api:'translator-text-api', translatorTextTier:'s1', standardTranslatedTextCharactersPayg`; ACS email: `emailsSentPerMonth`; microsoft-fabric: capacity SKU via select on layout.
New service → add via picker, dump fields (step 1), extend this list.

## Gotchas
- Calculator excludes the usage buffer and non-Azure licences; say so next to every link.
- Models not yet in the calculator (e.g. GPT-6 Sol/Luna) → price as nearest listed model and name it in `displayName`.
- Region slugs differ from ARM names: calculator `uae-north`, API `uaenorth`.
- Page slow when browser pane hidden: short scripts, `wait` actions in browser_batch, re-read store after each reload.
