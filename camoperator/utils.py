def positive_int(arg):
    n = int(arg)
    if n < 0:
        raise ValueError(f"Negative number ({arg}) is invalid")
    return n

def dimensions(arg):
    x, y = arg.split(',')
    return (positive_int(x), positive_int(y))
