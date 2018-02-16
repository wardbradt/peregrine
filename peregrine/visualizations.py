from async_build_markets import build_arbitrage_graph_for_exchanges
from async_build_markets import build_graph_for_exchanges
import networkx as nx
import ccxt

print(ccxt.exchanges)

# G = build_graph_for_exchanges(['bittrex', 'bitstamp', 'quoinex'])
# G2 = build_arbitrage_graph_for_exchanges(['bittrex', 'bitstamp', 'quoinex'])
#
# nx.drawing.nx_pydot.to_pydot(G).write_png('exchange_graph.png')
# nx.drawing.nx_pydot.to_pydot(G2).write_png('arbitrage_graph.png')
