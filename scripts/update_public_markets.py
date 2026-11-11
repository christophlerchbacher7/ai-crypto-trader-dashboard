"""Anonymous Kraken Spot ticker updater for the public site. No account access."""
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

PAIRS = {"BTC":"XBTEUR","ETH":"ETHEUR","SOL":"SOLEUR","XRP":"XRPEUR","DOGE":"DOGEEUR","ADA":"ADAEUR"}

def parse_ticker(payload, symbol):
    if not isinstance(payload,dict) or payload.get("error") != []:
        raise ValueError("Public Kraken API rejected request")
    result=payload.get("result")
    if not isinstance(result,dict) or len(result)!=1:
        raise ValueError("Ambiguous ticker")
    row=next(iter(result.values()))
    quotes={}
    for target,source in (("last_eur","c"),("bid_eur","b"),("ask_eur","a")):
        field=row.get(source) if isinstance(row,dict) else None
        if not isinstance(field,list) or len(field)<1:
            raise ValueError("Missing ticker quote")
        num=float(field[0])
        if not math.isfinite(num) or num<=0:
            raise ValueError("Invalid quote")
        quotes[target]=round(num,8)
    if quotes["ask_eur"] < quotes["bid_eur"]:
        raise ValueError("Crossed quote")
    return {"symbol":symbol,**quotes}

def request_ticker(pair):
    url="https://api.kraken.com/0/public/Ticker?pair="+quote(pair,safe="")
    req=Request(url,headers={"User-Agent":"Public-Kraken-Research/1.0","Accept":"application/json"})
    with urlopen(req,timeout=15) as response:
        if response.status != 200:
            raise ValueError("Invalid public HTTP status")
        data=response.read(150001)
    if len(data)>150000:
        raise ValueError("Response too large")
    return json.loads(data)

def build_snapshot(fetch=request_ticker,now=None):
    now=now or datetime.now(timezone.utc)
    markets=[parse_ticker(fetch(pair),symbol) for symbol,pair in PAIRS.items()]
    return {"source":"KRAKEN_PUBLIC_TICKER",
            "as_of":now.isoformat().replace("+00:00","Z"),
            "account_data":False,"execution_enabled":False,
            "markets":markets}

def main():
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python scripts/update_public_markets.py markets-public.json")
    snapshot=build_snapshot()
    Path(sys.argv[1]).write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Public Kraken market snapshot validated: "+str(len(snapshot["markets"]))+" symbols")

if __name__=="__main__":
    main()
