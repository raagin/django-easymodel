__all__ = (
    'languagecode',  'standin', 'first_match',
)


def first_match(predicate, lst):
    """
    returns the first value of predicate applied to list, which
    does not return None

    >>>
    >>> def return_if_even(x):
    ...     if x % 2 is 0:
    ...         return x
    ...     return None
    >>>
    >>> first_match(return_if_even, [1, 3, 4, 7])
    4
    >>> first_match(return_if_even, [1, 3, 5, 7])
    >>>

    :param predicate: a function that returns None or a value.
    :param list: A list of items that can serve as input to ``predicate``.
    :rtype: whatever ``predicate`` returns instead of None. (or None).
    """
    for item in lst:
        val = predicate(item)
        if val is not None:
            return val

    return None