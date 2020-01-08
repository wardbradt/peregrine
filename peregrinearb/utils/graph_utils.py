def get_greatest_edge_in_bunch(edge_bunch, weight='weight'):
    """
    Edge bunch must be of the format (u, v, d) where u and v are the tail and head nodes (respectively) and d is a list
    of dicts holding the edge_data for each edge in the bunch

    Not optimized because currently the only place that calls it first checks len(edge_bunch[2]) > 0
    todo: could take only edge_bunch[2] as parameter
    todo: not needed for this project: could put in wardbradt/networkx
    """
    if len(edge_bunch[2]) == 0:
        raise ValueError("Edge bunch must contain more than one edge.")
    greatest = {weight: -float('Inf')}
    for data in edge_bunch[2]:
        if data[weight] > greatest[weight]:
            greatest = data

    return greatest


def get_least_edge_in_bunch(edge_bunch, weight='weight'):
    """
    Edge bunch must be of the format (u, v, d) where u and v are the tail and head nodes (respectively) and d is a list
    of dicts holding the edge_data for each edge in the bunch

    todo: add this to some sort of utils file/ module in wardbradt/networkx
    """
    if len(edge_bunch[2]) == 0:
        raise ValueError("Edge bunch must contain more than one edge.")

    least = {weight: float('Inf')}
    for data in edge_bunch[2]:
        if data[weight] < least[weight]:
            least = data

    return least
