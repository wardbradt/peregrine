def next_to_each_other(li: list, *args):
    """
    Tests if the elements in args are present in the list in the order that they are given
    todo: is there an error if len(args) > len(li)?
    Examples
    --------
    >>> l = [0, 1, 2]
    >>> print(next_to_each_other(l, 1, 2)) # prints True
    >>> print(next_to_each_other(l, 0, 1)) # prints True
    >>> print(next_to_each_other(l, 2, 1)) # prints False
    >>> print(next_to_each_other(l, 0, 2)) # prints False

    Thanks in part to
    https://stackoverflow.com/questions/32533820/checking-items-in-a-list-to-see-if-they-are-beside-each-other
    """
    for i in range(len(li) - (len(args) - 1)):
        for j in range(len(args)):
            if li[i + j] != args[j]:
                break
            if j == len(args) - 1:
                return True
    return False


def last_index_in_list(li: list, element):
    """
    Thanks to https://stackoverflow.com/questions/6890170/how-to-find-the-last-occurrence-of-an-item-in-a-python-list
    """
    return len(li) - next(i for i, v in enumerate(reversed(li), 1) if v == element)
