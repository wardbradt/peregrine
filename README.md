# Peregrine

A Python library which provides several algorithms to detect arbitrage opportunities across over 90 cryptocurrency markets in 34 countries.

## Finding Arbitrage Opportunities: Example Usage

This section provides a brief overview of Peregrine's functionality. Examples demonstrating many more features are available in [peregrine/examples](https://github.com/wardbradt/peregrine/tree/master/examples).

### Multiples Exchange/ One Currency

```python
from peregrine import get_opportunity_for_market

opportunity = get_opportunity_for_market("BTC/USD")
print(opportunity)
```

At the time of writing, this prints the following in less than one second.

```py
{'highest_bid': {'exchange': <ccxt.async.lakebtc.lakebtc object at 0x10ea50518>, 'amount': 11750.59},
'lowest_ask': {'exchange': <ccxt.async.gdax.gdax object at 0x10ea50400>, 'amount': 8450.01}}
```

If you want to specify which exchanges to find opportunities on:

```py
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
from peregrine import load_exchange_graph, print_profit_opportunity_for_path, bellman_ford
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

### Multiple Exchanges/ Multiple Currencies

```python
from peregrine import create_weighted_multi_exchange_digraph, bellman_ford_multi, print_profit_opportunity_for_path_multi


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

## To Do

* Implement a fix to convert from USDT to USD and back again for markets based on USDT
* Package for pip
* Write better/ more examples and unit tests

## Potential Enhancements

* Create (better) data visualizations (The Networkx [documentation](https://networkx.github.io/documentation/stable/reference/drawing.html) provides some useful guides on drawing Networkx graphs)
* Implement machine learning to see which markets or exchanges consistently host the greatest disparities
* Update cythonperegrine to reflect some of the changes to peregrine
* Update doc strings to the same [standard](https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt#docstring-standard) as NumPy and SciPy
* Research [this paper](http://www.quantumforquants.org/quantum-computing/qa-arbitrage/) which discusses a more efficient way of finding the best arbitrage opportunity. It would take much work to implement but if someone with experience in quantum computing could help me that would be great.
* Related to the above, implement feature to find maximally profitable arbitrage opportunity.
* Implement `amount` parameter in bellman_ford to find cycles using at maximum the given amount.
* Research each exchange's fees and hard-code them (optionally into ccxt's Exchange objects) to account for fees when searching for opportunities.
