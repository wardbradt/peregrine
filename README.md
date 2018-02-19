# Peregrine
Detects arbitrage opportunities across 93 cryptocurrency markets in 34 countries

An extension of the asynchronous feature set of the [CCXT](https://github.com/ccxt/ccxt/) cryptocurrency trading library offering a Python and a Cython version

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
If you want to specify which exchanges to find opportunities on:
```
from peregrine import get_opportunity_for_market

opportunity = get_opportunity_for_market("BTC/USD", exchange_list=["anxpro", "bitbay", "coinfloor", "gemini", "livecoin"])
print(opportunity)
```

If you want to find opportunities on the exchanges of only a certain country<sup>1</sup>, you can do it like so:
```
from peregrine import build_specific_collections, get_opportunity_for_market

us_eth_btc_exchanges = build_specific_collections({'countries': 'US' })
opportunity = get_opportunity_for_market("ETH/BTC", us_eth_btc_exchanges["ETH/BTC"])
print(opportunity)
```
<sup>1</sup>Accepted arguments in place of "US" in this example are Austria, Australia, Bulgaria, Brazil, British Virgin Islands, Canada, China, Czech Republic, EU, Germany, Hong Kong, Iceland, India, Indonesia, Israel, Japan, Mexico, New Zealand, Panama, Philippines, Poland, Russia, Seychelles, Singapore, South Korea, St. Vincent & Grenadines, Sweden, Tanzania, Thailand, Turkey, UK, Ukraine, and Vietnam.
## To Do
* Implement a fix to convert from USDT to USD and back again for markets based on USDT
* Package for pip
* Allow exchange objects (instead of exchange names) to be used as arguments for functions in several files (namely async_find_opportunities.py)
* Write better examples and unit tests
* Make a utils directory instead of file, refactor functions into separate files (grouping by similarity)
## Potential Enhancements
* Create data visualizations (The Networkx [documentation](https://networkx.github.io/documentation/stable/reference/drawing.html) provides some useful guides on drawing Networkx graphs)
* Implement machine learning to see which markets or exchanges consistently host the greatest disparities
* Update cythonperegrine to reflect some of the changes to peregrine
