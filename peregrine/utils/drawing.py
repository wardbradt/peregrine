from subprocess import check_call

import networkx as nx


def draw_graph_to_file(graph, dot_name: str, to_file: str):
    nx.drawing.nx_pydot.write_dot(graph, dot_name + '.dot')
    check_call(['dot', '-Tpng', dot_name + '.dot', '-o', to_file])