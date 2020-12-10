from time import strftime, gmtime


def number_to_timeformat(number: int):
    return strftime("%H:%M:%S", gmtime(number))
