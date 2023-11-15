import numpy as np

# Initializes NNFS
def init(dot_precision_workaround=True, default_dtype='float32', random_seed=0):

    # Numpy methods to be replaced for a workaround
    methods_to_enclose = [
        [np, 'zeros', False, 1],
        [np.random, 'randn', True, None],
        [np, 'eye', False, 1],
    ]

    # https://github.com/numpy/numpy/issues/15591
    # np.dot() is not consistent between machines
    # This workaround raises consistency
    # we make computations using float64, but return float32 data
    if dot_precision_workaround:
        orig_dot = np.dot
        def dot(*args, **kwargs):
            return orig_dot(*[a.astype('float64') for a in args], **kwargs).astype('float32')
        np.dot = dot
    else:
        methods_to_enclose.append([np, 'dot', True, None])

    # https://github.com/numpy/numpy/issues/6860
    # It is not possible to set default datatype with numpy
    # To make it able to enable and disable above workaround and set dtype
    # we'll enclose numpy method's with own one which will force different datatype
    if default_dtype:
        for method in methods_to_enclose:
            enclose(method, default_dtype)

    # Set seed to the given value (0 by default)
    if random_seed is not None:
        np.random.seed(random_seed)

def create_spiral_data(samples, classes):
    X = np.zeros((samples*classes, 2))
    y = np.zeros(samples*classes, dtype='uint8')
    for class_number in range(classes):
        ix = range(samples*class_number, samples*(class_number+1))
        r = np.linspace(0.0, 1, samples)
        t = np.linspace(class_number*4, (class_number+1)*4, samples) + np.random.randn(samples)*0.2
        X[ix] = np.c_[r*np.sin(t*2.5), r*np.cos(t*2.5)]
        y[ix] = class_number
    return X, y


# Encloses numpy method
def enclose(method, default_dtype):

    # Save a handler to original method
    method.append(getattr(*method[:2]))
    def enclosed_method(*args, **kwargs):

        # If flag is True - use .astype()
        if method[2]:
            return method[4](*args, **kwargs).astype(default_dtype)

        # Else pass dtype in kwargs
        else:
            if len(args) <= method[3] and 'dtype' not in kwargs:
                kwargs['dtype'] = default_dtype
            return method[4](*args, **kwargs)

    # Replace numpy method with enclosed one
    setattr(*method[:2], enclosed_method)

def create_vertical_data(samples, classes):
    X = np.zeros((samples*classes, 2))
    y = np.zeros(samples*classes, dtype='uint8')
    for class_number in range(classes):
        ix = range(samples*class_number, samples*(class_number+1))
        X[ix] = np.c_[np.random.randn(samples)*.1 + (class_number)/3, np.random.randn(samples)*.1 + 0.5]
        y[ix] = class_number
    return X, y