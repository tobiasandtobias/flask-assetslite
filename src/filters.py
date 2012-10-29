from collections import namedtuple

# Named tuple which represents a filter command step.
Step = namedtuple('Step', ('command', 'kind'))


class Filter(list):
    """
    A filter is a list of commands through which data or a file will be
    piped. Each step requires both the `command` and a `kind`, which
    denotes how the command receives and outputs data.

    See `pipes.append()` in the Python documentation for more
    information.
    """
    def __init__(self, steps=[]):
        steps = steps if type(steps) is list else [steps]
        for step in steps:
            self.append((step[0], step[1]))

# Filters, pre-made with love
less = Filter(('lessc $IN', 'f-'))
cssmin = Filter(('cssmin', '--'))
uglifyjs = Filter(('uglifyjs', '--'))
