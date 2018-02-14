# import ccxt
# import networkx as nx
# import json
#
# with open('graph.json', 'r') as f:
#     data = json.load(f)
#     G = nx.from_dict_of_dicts(data, multigraph_input=True)
#     print(data)
#
# for exchange_name in ccxt.exchanges:
#     graph = initialize_completed_graph_for_exchange(exchange_name)

from async_build_markets import build_graph_for_exchanges
import ccxt
from bellman import initialize_completed_graph_for_exchange


for exchange_name in ccxt.exchanges:
    graph = initialize_completed_graph_for_exchange(exchange_name)
