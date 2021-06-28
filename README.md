# Peregrine

A Python library which provides several algorithms to detect arbitrage opportunities across over 120 cryptocurrency exchanges in 48 countries on over 38,000 trading pairs

I created this in 2017 as a proof-of-concept to familiarize myself with cryptocurrency arbitrage. 
I had fun building it, but do not presently have the bandwidth to maintain the repository. 
There are some known issues. 
See the [Future Development](#future-development) section to see current issues and ideas for improvement.


### [Install](#install) · [Usage](#usage) · [Future Development](#future-development) 

## Install
1. Ensure you have [installed pip](https://pip.pypa.io/en/stable/installing/).
2. Run the following in your command line:

    ```
    pip install git+https://github.com/wardbradt/peregrine
    ```
    
## Usage

This section provides a brief overview of Peregrine's functionality. Examples demonstrating many more features are available in [peregrine/examples](https://github.com/wardbradt/peregrine/tree/master/examples).

### Multiples Exchange/ One Currency

```python
from peregrinearb import get_opportunity_for_market
import asyncio
collections_dir = '/Users/wardbradt/cs/peregrine/'
opportunity = asyncio.get_event_loop().run_until_complete(get_opportunity_for_market("BTC/USD", collections_dir))
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

collections_dir = '/Users/wardbradt/cs/peregrine/'
opportunity = asyncio.get_event_loop().run_until_complete(get_opportunity_for_market("BTC/USD", collections_dir, exchanges=["anxpro", "bitbay", "coinfloor", "gemini", "livecoin"]))
print(opportunity)
```

If you want to find opportunities on the exchanges of only a certain country<sup>1</sup>, you can do it like so:

```python
from peregrinearb import build_specific_collections, get_opportunity_for_market

us_eth_btc_exchanges = build_specific_collections(countries=['US'])
collections_dir = '/Users/wardbradt/cs/peregrine/'
opportunity = get_opportunity_for_market("ETH/BTC", collections_dir, us_eth_btc_exchanges["ETH/BTC"])
print(opportunity)
```

<sup>1</sup>Accepted arguments in place of 'US' in this example are 'PA', 'AU', 'CA', 'JP', 'SG', 'HK', 'NZ', 'IE', 'CN', 'KR', 'IL', 'MT', 'EU', 'VG', 'GB', 'RU', 'PL', 'SC', 'MX', 'NL', 'BR', 'PH', 'UA', 'TR', 'IS', 'TH', 'DE', 'CY', 'CL', 'TW', 'ID', 'UK', 'IN', 'VN', 'BG', 'CZ', 'ES', 'SE', 'VC', 'ZA', 'CH', 'TZ', 'FR', 'AR', 'VE', 'PK', and 'AT'.

### One Exchange/ Multiple Currencies

```python
import asyncio
from peregrinearb import load_exchange_graph, print_profit_opportunity_for_path, bellman_ford
graph = asyncio.get_event_loop().run_until_complete(load_exchange_graph('hitbtc'))

paths = bellman_ford(graph)
for path in paths:
    print_profit_opportunity_for_path(graph, path)
```

This prints all of the arbitrage opportunities on the given exchange (in this case, HitBTC). At the time of writing, the first opportunity printed out is:

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

graph = asyncio.get_event_loop().run_until_complete(load_exchange_graph('gdax', fees=True))

paths = bellman_ford(graph)
for path in paths:
    print_profit_opportunity_for_path(graph, path)
```

To find the maximum volume that can be used to execute the opportunity, set `depth=True` when calling `bellman_ford`. To my knowledge, the only exchange which offers the functionality of simultaneously fetching the volumes of the top price levels for all markets is Binance.
```python
import asyncio
from peregrinearb import load_exchange_graph, print_profit_opportunity_for_path, bellman_ford

graph = asyncio.get_event_loop().run_until_complete(load_exchange_graph('binance'))

paths = bellman_ford(graph, depth=True)
for path, starting_amount in paths:
    # Note that depth=True and starting_amount are set in this example
    print_profit_opportunity_for_path(graph, path, depth=True, starting_amount=starting_amount)
```
This would output:
```
Starting with 0.25 in BTC
BTC to USDT at 7955.100000 = 1988.775
USDT to NEO at 0.016173 = 32.1652110625
NEO to ETH at 0.110995 = 3.5701776025
ETH to XLM at 2709.292875 = 9,672.65673772
XLM to BTC at 0.000026 = 0.25052181
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

## Future Development
I do not presently actively maintain this project but will respond to issues and pull requests.

### Issues
See the repository's [Issues](https://github.com/wardbradt/peregrine/issues) tab for user-submitted issues. At the time of writing, issues I am aware of are:
- async functionality may be broken
- some issues with relative paths to generated json files

### Enhancements

Improvements that would be appreciated:

- Prune graph into connected components to improve runtimne
- Split graph into cycles to find most profitable, instead of any, arbitrage opportunity
    - A good algorithm to do this is [Johnson's 1975 Cycle-Finding Algorithm](https://www.cs.tufts.edu/comp/150GA/homeworks/hw1/Johnson%2075.PDF)
- Update requirements and Python version
