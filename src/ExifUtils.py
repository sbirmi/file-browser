import datetime
import re

def parse_exif_timestamp(inp):
    """
    Input format '2019:09:21 15:17:06.167'
    Returns python datetime object
    """
    assert inp
    if not hasattr(parse_exif_timestamp, "reg"):
        parse_exif_timestamp.reg = re.compile("(?P<year>\d\d\d\d):(?P<month>\d\d):(?P<day>\d+)\s+"
                                              "(?P<hour>\d+):(?P<minute>\d+):(?P<second>\d+)")

    match = parse_exif_timestamp.reg.match(inp)
    assert match

    return datetime.datetime(*list(map(int, match.groups())))

def from_exif_timestamp(*inps):
    """
    Returns the first datetime that can be parsed
    """
    for inp in inps:
        try:
            dt = parse_exif_timestamp(inp)
        except Exception as exc:
            print("Failed", inp, exc)
            continue
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    assert False, "Couldn't parse any of the dates: " + str(inps)

