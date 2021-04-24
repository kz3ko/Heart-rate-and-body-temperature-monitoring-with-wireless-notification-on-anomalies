def sum(data):
    """
    Get sum of list elements.
    """
    result = 0
    for value in data:
        result += value
    return result

def mean(data):
    """
    Get mean value of all list elements.
    """
    return sum(data)/len(data)

def abs(value):
    """
    Get abs value of value.
    """
    if value < 0:
        value = -value
    else:
        pass
    return value
