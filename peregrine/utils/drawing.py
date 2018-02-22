import networkx as nx


def draw_graph_to_png(graph, to_file: str):
    nx.drawing.nx_pydot.to_pydot(graph).write_png(to_file)
