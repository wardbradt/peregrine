import math
import networkx as nx


class NegativeWeightFinder:

    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.predecessor = {}
        self.distance_to = {}
    
    def initialize(self, source):
        for node in self.graph:
            # Initialize all distance_to values to infinity and all predecessor values to None
            self.distance_to[node] = float('Inf')
            self.predecessor[node] = None
        # The distance from any node to (itself) == 0
        self.distance_to[source] = 0

    def bellman_ford(self, source):
        """
        :param source: The node in graph from which the values in distance_to will be calculated.
        """
        self.initialize(source)
        # After len(graph) - 1 passes, algorithm is complete.
        for i in range(len(self.graph) - 1):
            # for each node in the graph, test if the distance to each of its siblings is shorter by going from
            # source->base_currency + base_currency->quote_currency
            for edge in self.graph.edges(data=True):
                if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                    self.distance_to[edge[1]] = self.distance_to[edge[0]] + edge[2]['weight']
                    self.predecessor[edge[1]] = edge[0]

        for edge in self.graph.edges(data=True):
            if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                return retrace_negative_loop(self.predecessor, source)

        return None


def bellman_ford(graph, source):
    return NegativeWeightFinder(graph).bellman_ford(source)


def retrace_negative_loop(predecessor, start):
    arbitrage_loop = [start]
    next_node = start
    while True:
        next_node = predecessor[next_node]
        if next_node not in arbitrage_loop:
            arbitrage_loop.insert(0, next_node)
        else:
            arbitrage_loop.insert(0, next_node)
            arbitrage_loop = arbitrage_loop[arbitrage_loop.index(next_node):]
            return arbitrage_loop


def calculate_profit_ratio_for_path(graph, path):
    money = 1
    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            # todo: rate should not have to be inversed
            rate = 1 / math.exp(-graph[start][end])
            money *= rate
    return money


def print_profit_opportunity_for_path(graph, path):
    money = 100
    print("Starting with %(money)i in %(currency)s" % {"money": money, "currency": path[0]})

    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            # todo: rate should not have to be inversed
            rate = math.exp(-graph[start][end]['weight'])
            money *= rate
            print("%(start)s to %(end)s at %(rate)f = %(money)f" % {"start": start, "end": end, "rate": rate,
                                                                    "money": money})


# G = load_exchange_graph('bittrex')
# print(G)
graph = nx.DiGraph()
graph.add_edge(0, 1, weight=-math.log(2))
graph.add_edge(1, 0, weight=math.log(2))

graph.add_edge(1, 2, weight=-math.log(6/5))
graph.add_edge(2, 1, weight=math.log(6/5))

graph.add_edge(2, 0, weight=-math.log(7/12))
graph.add_edge(0, 2, weight=math.log(7/12))

graph.add_edge(1, 3, weight=-math.log(3))
graph.add_edge(3, 1, weight=math.log(3))

graph.add_edge(0, 3, weight=-math.log(3))
graph.add_edge(3, 0, weight=math.log(3))

n = NegativeWeightFinder(graph)
path = n.bellman_ford(0)
print_profit_opportunity_for_path(graph, path)


# graph = create_exchange_graph(getattr(ccxt, 'bittrex')())
#
# path = NegativeWeightFinder(getattr(ccxt, 'bittrex')()).bellman_ford(0)
# print(path)
