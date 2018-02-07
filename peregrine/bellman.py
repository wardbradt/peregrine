import math
import ccxt


def download(exchange_name):
    graph = {}
    exchange = getattr(ccxt, exchange_name)()
    exchange.load_markets()

    for market_name, market_info in exchange.markets.items():
        # for now, treating price as average of ask and bid
        ticker_price = (exchange.fetch_ticker(market_name)['ask'] + exchange.fetch_ticker(market_name)['bid']) / 2
        # prevent math error when Bittrex (GEO/BTC) or other API gives 0 as ticker price
        if ticker_price == 0:
            continue
        conversion_rate = -math.log(ticker_price)

        from_currency, to_currency = market_name.split('/')
        if from_currency not in graph:
            graph[from_currency] = {}
        graph[from_currency][to_currency] = float(conversion_rate)
    return graph


# Step 1: For each node prepare the destination and predecessor
def initialize(graph, source):
    destination = {}
    predecessor = {}
    for node in graph:
        # Initialize distTo all values to infinity
        destination[node] = float('Inf')
        predecessor[node] = None
    destination[source] = 0  # For the source we know how to reach
    return destination, predecessor


def relax(node, neighbour, graph, d, p):
    # If the distance between the node and the neighbour is lower than the one I have now
    if d[neighbour] > d[node] + graph[node][neighbour]:
        # Record this lower distance
        d[neighbour] = d[node] + graph[node][neighbour]
        p[neighbour] = node


def retrace_negative_loop(p, start):
    arbitrage_loop = [start]
    next_node = start
    while True:
        next_node = p[next_node]
        if next_node not in arbitrage_loop:
            arbitrage_loop.append(next_node)
        else:
            arbitrage_loop.append(next_node)
            arbitrage_loop = arbitrage_loop[arbitrage_loop.index(next_node):]
            return arbitrage_loop


def bellman_ford(graph, source):
    d, p = initialize(graph, source)
    for i in range(len(graph) - 1):  # Run this until is converges
        for u in graph:
            for v in graph[u]:  # For each neighbour of u
                relax(u, v, graph, d, p)  # Lets relax it

    # Step 3: check for negative-weight cycles
    for u in graph:
        for v in graph[u]:
            if d[v] < d[u] + graph[u][v]:
                return retrace_negative_loop(p, source)
    return None


paths = []

graph = download('bittrex')

for key in graph:
    path = bellman_ford(graph, key)
    if path not in paths and not None:
        paths.append(path)

for path in paths:
    if path is None:
        print("No opportunity here :(")
    else:
        money = 100
        print("Starting with %(money)i in %(currency)s" % {"money": money, "currency": path[0]})

        for i, value in enumerate(path):
            if i + 1 < len(path):
                start = path[i]
                end = path[i + 1]
                rate = math.exp(-graph[start][end])
                money *= rate
                print("%(start)s to %(end)s at %(rate)f = %(money)f" % {"start": start, "end": end, "rate": rate,
                                                                        "money": money})
