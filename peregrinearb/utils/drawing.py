import networkx as nx
import json

__all__ = [
    'accepted_types',
    'draw_graph_to_png',
    'format_graph_for_json',
    'write_graph_to_json',
    'multi_digraph_from_dict',
    'multi_digraph_from_json',
    'digraph_from_dict',
]


accepted_types = {nx.MultiDiGraph: 'MultiDiGraph', nx.MultiGraph: 'MultiGraph', nx.DiGraph: 'DiGraph',
                  nx.Graph: 'Graph'}


def draw_graph_to_png(graph, to_file: str):
    nx.drawing.nx_pydot.to_pydot(graph).write_png(to_file)


def format_graph_for_json(graph, raise_errors=True):
    """
    Currently, only supported types for graph are Graph, DiGraph, MultiGraph, and MultiDiGraph. graph must
    be an instance of one of these types, not a class that inherits from one.
    """
    graph_dict = nx.to_dict_of_dicts(graph)
    graph_type = ''

    for key, value in accepted_types.items():
        if type(graph) == key:
            graph_type = value
            break

    if graph_type == '':
        if raise_errors:
            raise TypeError('parameter graph is not of the accepted types.graph is of'
                            'type {}'.format(str(type(graph))))
        else:
            graph_type = 'other'

    return {'graph_type': graph_type, 'graph_dict': graph_dict}


def write_graph_to_json(graph, to_file: str, raise_errors=True):
    result = format_graph_for_json(graph, raise_errors=raise_errors)
    with open(to_file, 'w') as outfile:
        json.dump(result, outfile)

    return result


def multi_digraph_from_json(file_name: str):
    with open(file_name) as data:
        data = json.load(data)
    return multi_digraph_from_dict(data)


def digraph_from_dict(data):
    G = nx.DiGraph()
    for node in data.keys():
        neighbors = data[node]
        for neighbor, attributes in neighbors.items():
            G.add_edge(node, neighbor, weight=attributes["weight"])
    return G


def multi_digraph_from_dict(data):
    G = nx.MultiDiGraph()
    for node in data.keys():
        neighbors = data[node]
        for neighbor, v in neighbors.items():
            for data_dict in v.values():
                G.add_edge(node, neighbor, **data_dict)

    return G
