def elements_next_to_each_other(list_to_check: list, *args):
    """
    Tests if the elements in args are present in the list in the order that they are given

    Examples
    --------
    >>> l = [0, 1, 2]
    >>> print(elements_next_to_each_other(l, 1, 2)) # prints True
    >>> print(elements_next_to_each_other(l, 0, 1)) # prints True
    >>> print(elements_next_to_each_other(l, 2, 1)) # prints False
    >>> print(elements_next_to_each_other(l, 0, 2)) # prints False

    Thanks in part to
    https://stackoverflow.com/questions/32533820/checking-items-in-a-list-to-see-if-they-are-beside-each-other
    """
    for i in range(len(list_to_check) - (len(args) - 1)):
        for j in range(len(args)):
            if list_to_check[i + j] != args[j]:
                break
            if j == len(args) - 1:
                return True
    return False
