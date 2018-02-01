# peregrine-scout
Detects arbitrage opportunities across 93 cryptocurrency markets

An extension of the asynchronous feature set of the [CCXT](https://github.com/ccxt/ccxt/) cryptocurrency trading library

## Example Usage
```
from peregrine import get_opportunity_for_market

opportunity = get_opportunity_for_market("BTC/USD")
print(opportunity)
```
At the time of writing, this prints the following in less than one second.
```
{'highest_bid': {'exchange': <ccxt.async.lakebtc.lakebtc object at 0x10ea50518>, 'amount': 11750.59}, 
'lowest_ask': {'exchange': <ccxt.async.gdax.gdax object at 0x10ea50400>, 'amount': 8450.01}}
```

## Todo:
Create a tool to identify which exchanges take abnormally long to respond to API requests.
