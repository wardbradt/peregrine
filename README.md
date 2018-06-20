# Peregrine

A Python library which provides several algorithms to detect arbitrage opportunities across over 90 cryptocurrency exchanges in 34 countries

## Installation
1. Ensure you have [installed pip](https://pip.pypa.io/en/stable/installing/).
2. Run the following in your command line:
```
pip install peregrinearb
```

## Finding Arbitrage Opportunities: Example Usage

This section provides a brief overview of Peregrine's functionality. Examples demonstrating many more features are available in [peregrine/examples](https://github.com/wardbradt/peregrine/tree/master/examples).

### Multiples Exchange/ One Currency

```python
from peregrinearb import get_opportunity_for_market
import asyncio
opportunity = asyncio.get_event_loop().run_until_complete(get_opportunity_for_market("BTC/USD"))
print(opportunity)
```

At the time of writing, this prints the following in less than one second.

```
{'highest_bid': {'exchange': <ccxt.async.lakebtc.lakebtc object at 0x10ea50518>, 'price': 11750.59},
'lowest_ask': {'exchange': <ccxt.async.gdax.gdax object at 0x10ea50400>, 'price': 8450.01}}
```

If you want to specify which exchanges to find opportunities on:

```python
from peregrinearb import get_opportunity_for_market
import asyncio

opportunity = asyncio.get_event_loop().run_until_complete(get_opportunity_for_market("BTC/USD", exchange_list=["anxpro", "bitbay", "coinfloor", "gemini", "livecoin"]))
print(opportunity)
```

If you want to find opportunities on the exchanges of only a certain country<sup>1</sup>, you can do it like so:

```python
from peregrinearb import build_specific_collections, get_opportunity_for_market

us_eth_btc_exchanges = build_specific_collections('countries'=['US'])
opportunity = get_opportunity_for_market("ETH/BTC", us_eth_btc_exchanges["ETH/BTC"])
print(opportunity)
```

<sup>1</sup>Accepted arguments in place of "US" in this example are Austria, Australia, Bulgaria, Brazil, British Virgin Islands, Canada, China, Czech Republic, EU, Germany, Hong Kong, Iceland, India, Indonesia, Israel, Japan, Mexico, New Zealand, Panama, Philippines, Poland, Russia, Seychelles, Singapore, South Korea, St. Vincent & Grenadines, Sweden, Tanzania, Thailand, Turkey, UK, Ukraine, and Vietnam.

### One Exchange/ Multiple Currencies

```python
import asyncio
from peregrinearb import load_exchange_graph, print_profit_opportunity_for_path, bellman_ford
graph = asyncio.get_event_loop().run_until_complete(load_exchange_graph('binance'))

paths = bellman_ford(graph, 'BTC')
for path in paths:
    print_profit_opportunity_for_path(graph, path)
```

This prints all of the arbitrage opportunities on the given exchange (in this case, Binance). At the time of writing, the first opportunity printed out is:

```
Starting with 100 in BTC
BTC to USDT at 7955.100000 = 795510.000000
USDT to NEO at 0.016173 = 12866.084425
NEO to ETH at 0.110995 = 1428.071041
ETH to XLM at 2709.292875 = 3869062.695088
XLM to BTC at 0.000026 = 100.208724
```
If you would like to account for transaction fees, set `fees=True` when calling `load_exchange_graph`.
```python
import asyncio
from peregrinearb import load_exchange_graph, print_profit_opportunity_for_path, bellman_ford


loop = asyncio.get_event_loop()
graph = loop.run_until_complete(load_exchange_graph('binance', fees=True))

paths = bellman_ford(graph, 'BTC', unique_paths=True)
for path in paths:
    print_profit_opportunity_for_path(graph, path)
```

### Multiple Exchanges/ Multiple Currencies

```python
from peregrinearb import create_weighted_multi_exchange_digraph, bellman_ford_multi, print_profit_opportunity_for_path_multi


graph = create_weighted_multi_exchange_digraph(['kraken', 'bittrex', 'gemini'], log=True)
graph, paths = bellman_ford_multi(graph, 'ETH')
for path in paths:
    print_profit_opportunity_for_path_multi(graph, path)
```

This prints all of the arbitrage opportunities on the given exchanges. At the time of writing, the first opportunity printed out is:

```
Starting with 100 in ETH
ETH to ANT at 204.26088199848851 = 20426.08819984885 on bittrex for ANT/ETH
ANT to BTC at 0.00034417000000000003 = 7.03004677574198 on bittrex for ANT/BTC
BTC to MLN at 136.57526594618665 = 960.1305080110928 on bittrex for MLN/BTC
MLN to BTC at 0.0073799999999999985 = 7.085763149121863 on kraken for MLN/BTC
BTC to GNO at 98.03921568627446 = 694.6826616786137 on bittrex for GNO/BTC
GNO to BTC at 0.010300000000000002 = 7.155231415289722 on kraken for GNO/BTC
BTC to GNO at 98.03921568627446 = 701.493276008796 on bittrex for GNO/BTC
GNO to BTC at 0.010300000000000002 = 7.2253807428906 on kraken for GNO/BTC
BTC to MLN at 136.57526594618665 = 986.8082965227394 on bittrex for MLN/BTC
MLN to BTC at 0.0073799999999999985 = 7.282645228337815 on kraken for MLN/BTC
BTC to USD at 7964.809999999999 = 58004.8855411173 on gemini for BTC/USD
USD to ETH at 0.0017965900720432618 = 104.21100149317708 on kraken for ETH/USD
```
Should you like to account for transaction fees. In the example above, simply set `fees` to `True` when calling `create_weighted_multi_exchange_digraph`.
For example, the following code prints out all of the opportunities found on the given exchanges while accounting for fees:
```python
from peregrinearb import create_weighted_multi_exchange_digraph, bellman_ford_multi, print_profit_opportunity_for_path_multi


graph = create_weighted_multi_exchange_digraph(['exmo', 'binance', 'bitmex', 'bittrex', 'gemini', 'kraken'], log=True)


graph, paths = bellman_ford_multi(graph, 'ETH', unique_paths=True)
for path in paths:
    # total = calculate_profit_ratio_for_path(graph, path)
    # print(path)
    print_profit_opportunity_for_path_multi(graph, path)
```
The most profitable of the two printed out is:
```
Starting with 100 in ETH
ETH to LTC at 3.2955444239388347 = 329.55444239388345 on binance for LTC/ETH
LTC to USD at 173.00829999999996 = 57015.65383601369 on exmo for LTC/USD
USD to XRP at 1.4110342881332016 = 80451.04252294863 on kraken for XRP/USD
XRP to USD at 0.739201 = 59469.49108400615 on exmo for XRP/USD
USD to BTC at 0.00011205737337516807 = 6.663994966831705 on bitmex for BTC/USD
BTC to XRP at 12599.218848431392 = 83961.13099195795 on bittrex for XRP/BTC
XRP to USD at 0.739201 = 62064.15199038631 on exmo for XRP/USD
USD to BTC at 0.00011205737337516807 = 6.954745852799899 on bitmex for BTC/USD
BTC to XRP at 12599.218848431392 = 87624.36503464654 on bittrex for XRP/BTC
XRP to RUB at 39.120000000000005 = 3427865.160155373 on exmo for XRP/RUB
RUB to USD at 0.018667164457718873 = 63988.522683505194 on exmo for USD/RUB
USD to XRP at 1.4110342881332016 = 90289.99955341498 on kraken for XRP/USD
XRP to RUB at 39.120000000000005 = 3532144.7825295944 on exmo for XRP/RUB
RUB to USD at 0.018667164457718873 = 65935.1275439536 on exmo for USD/RUB
USD to BCH at 0.000949667616334283 = 62.61645540736334 on kraken for BCH/USD
BCH to ETH at 1.8874401 = 118.18480885571941 on bittrex for BCH/ETH
```

## To Do

* Implement a fix to convert from USDT to USD and back again for markets based on USDT
* Package for pip
* Write better/ more examples and unit tests
* Fix frequent `Unclosed connector` ccxt error (look at [this issue](https://github.com/ccxt/ccxt/issues/2092))
## Potential Enhancements

* Create (better) data visualizations (The Networkx [documentation](https://networkx.github.io/documentation/stable/reference/drawing.html) provides some useful guides on drawing Networkx graphs)
* Implement machine learning to see which markets or exchanges consistently host the greatest disparities
* Update cythonperegrine to reflect some of the changes to peregrine
* Update doc strings to the same [standard](https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt#docstring-standard) as NumPy and SciPy
* Research [this paper](http://www.quantumforquants.org/quantum-computing/qa-arbitrage/) which discusses a more efficient way of finding the best arbitrage opportunity. It would take much work to implement but if someone with experience in quantum computing could help me that would be great.
* Related to the above, implement feature to find maximally profitable arbitrage opportunity.
* Implement `amount` parameter in bellman_ford to find cycles using at maximum the given amount.
* Research each exchange's fees and hard-code them (optionally into ccxt's Exchange objects) to account for fees when searching for opportunities.

## Tips
If you have benefitted from Peregrine and would like to show your appreciation, feel free to send funds to any of the following addresses:
```
ETH 0x75B00bA659a6BF735Cf039eE1B04b84fa7a84A83
```
