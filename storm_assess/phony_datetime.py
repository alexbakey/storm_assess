"""
Modifies the netcdftime.datetime class to support rich comparison operators.

In the future this code should be obsolete - please contact
ml-avd-support@metoffice.gov.uk if this is still in use after 1st June 2014 to
see whether a more general datetime class exists.

"""
import netcdftime


datetime = netcdftime.datetime


def add_to_netcdftime_datetime(func):
    """A decorator to add the function to the netcdftime.datetime class."""
    setattr(netcdftime.datetime, func.__name__, func)
    return func


@add_to_netcdftime_datetime
def __eq__(self, other):
    # netcdftime.datetime does not support microseconds.
    if not isinstance(other, netcdftime.datetime) and other.microsecond != 0:
        return False
    return self.timetuple()[:-3] == other.timetuple()[:-3]


@add_to_netcdftime_datetime
def __ne__(self, other):
    return not self == other


@add_to_netcdftime_datetime
def __lt__(self, other):
    # netcdftime.datetime does not support microseconds.
    if not isinstance(other, netcdftime.datetime) and other.microsecond != 0:
        return False
    s_tt = self.timetuple()[:-3]
    o_tt = other.timetuple()[:-3]
    if s_tt == o_tt:
        return False
    for s_elem, o_elem in zip(s_tt, o_tt):
        if s_elem < o_elem:
            return True
        elif s_elem > o_elem:
            return False
    raise RuntimeError('Whoa')


@add_to_netcdftime_datetime
def __gt__(self, other):
    # netcdftime.datetime does not support microseconds.
    if not isinstance(other, netcdftime.datetime) and other.microsecond != 0:
        return False
    s_tt = self.timetuple()[:-3]
    o_tt = other.timetuple()[:-3]
    if s_tt == o_tt:
        return False
    for s_elem, o_elem in zip(s_tt, o_tt):
        if s_elem > o_elem:
            return True
        elif s_elem < o_elem:
            return False
    return True


@add_to_netcdftime_datetime
def __ge__(self, other):
    return self == other or self > other 


@add_to_netcdftime_datetime
def __le__(self, other):
    return self == other or self < other