# Peregrine
Detects arbitrage opportunities across 93 cryptocurrency markets in 34 countries

An extension of the asynchronous feature set of the [CCXT](https://github.com/ccxt/ccxt/) cryptocurrency trading library offering a Python and a Cython version

In order to use the features that implement [Networkx](https://github.com/networkx/networkx), you must use [my fork](https://github.com/wardbradt/networkx) to avoid errors.

## Finding Arbitrage Opportunities: Example Usage
### Multiples Exchange/ One Currency
```python
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
```python
from peregrine import build_specific_collections, get_opportunity_for_market

us_eth_btc_exchanges = build_specific_collections({'countries': 'US' })
opportunity = get_opportunity_for_market("ETH/BTC", us_eth_btc_exchanges["ETH/BTC"])
print(opportunity)
```
<sup>1</sup>Accepted arguments in place of "US" in this example are Austria, Australia, Bulgaria, Brazil, British Virgin Islands, Canada, China, Czech Republic, EU, Germany, Hong Kong, Iceland, India, Indonesia, Israel, Japan, Mexico, New Zealand, Panama, Philippines, Poland, Russia, Seychelles, Singapore, South Korea, St. Vincent & Grenadines, Sweden, Tanzania, Thailand, Turkey, UK, Ukraine, and Vietnam.
### One Exchange/ Multiple Currencies
```python
import asyncio
from peregrine import load_exchange_graph, bellman_ford_multi, print_profit_opportunity_for_path
loop = asyncio.get_event_loop()
graph = loop.run_until_complete(load_exchange_graph('binance')) # load_exchange_graph is asynchronous
path = bellman_ford_multi(graph, 'LTC')
print_profit_opportunity_for_path(graph, path)
```
This prints the following in under a second (plus the time waiting for the API response from Binance):
```
Starting with 100 in BTC
BTC to AMB at 17943.656917 = 1794365.691728
AMB to BNB at 0.062210 = 111627.489682
BNB to USDT at 10.181700 = 1136557.611699
USDT to BCH at 0.000714 = 811.826865
BCH to BTC at 0.124012 = 100.676273
```
### Multiple Exchanges/ Multiple Currencies
```python
from peregrine import create_weighted_multi_exchange_digraph, bellman_ford_multi, print_profit_opportunity_for_path_multi


graph = create_weighted_multi_exchange_digraph(['exmo', 'bittrex', 'gemini'], log=True)
path = bellman_ford_multi(graph, 'ETH')
print_profit_opportunity_for_path_multi(graph, path)
```
This prints:
```
Starting with 100 in ETH
ETH to XRP at 875.848478213269 = 87584.8478213269 on bittrex for XRP/ETH
XRP to EUR at 0.83136 = 72814.53908473832 on kraken for XRP/EUR
EUR to XMR at 0.004197095609837993 = 305.6095823249322 on kraken for XMR/EUR
XMR to USDT at 295.1404826099999 = 90197.75961762098 on bittrex for XMR/USDT
USDT to NEO at 0.007932101213611488 = 715.4577585279686 on bittrex for NEO/USDT
NEO to ETH at 0.1410783 = 100.93556429493631 on bittrex for NEO/ETH
```
## To Do
* Implement a fix to convert from USDT to USD and back again for markets based on USDT
* Package for pip
* Allow exchange objects (instead of exchange names) to be used as arguments for functions in several files (namely async_find_opportunities.py)
* Write better examples and unit tests
* Refactor bellmannx.py and bellman_multi_exchange.py to avoid two functions both named `bellman_ford_multi`
* Fix `print_profit_opportunity_for_path` (look at comment in bellman_multi_graph.py for more information)
## Potential Enhancements
* Create (better) data visualizations (The Networkx [documentation](https://networkx.github.io/documentation/stable/reference/drawing.html) provides some useful guides on drawing Networkx graphs)
* Implement machine learning to see which markets or exchanges consistently host the greatest disparities
* Update cythonperegrine to reflect some of the changes to peregrine
* Update doc strings to the same [standard](https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt#docstring-standard) as NumPy and SciPy