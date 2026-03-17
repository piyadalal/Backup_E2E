import datetime as dt


def unicodeSafe(s):
    if getattr(s, 'encode', None) and (type(s) == str):
        s = s.encode("utf8")
    return s


def ymdString(addDays=0):
    now = dt.datetime.now()
    addDate = now + dt.timedelta(days=addDays)
    s = addDate.strftime("%Y%m%d")
    return s


def parse_eid(eid, raw_eid=False):
    """
    Return a event ID as a string, suitable for comparison with event DB data.

    :param eid: hex-coded eid, as sent by API.
    :param raw_eid: keep eid in its original form, parse it otherwise (default).
    """

    service_key = event_id = None

    parts = eid.split("-")
    if len(parts) > 1:
        if len(parts) == 2:
            service_key_hex = parts[0][1:]  # drop first letter, the E they add to every eid
            event_id_hex = parts[1]

            service_key_int_value = int(service_key_hex, base=16)
            event_id_int_value = int(event_id_hex, base=16)

            service_key = str(service_key_int_value)
            event_id = str(event_id_int_value)
        else:
            service_key = '-'.join(parts[:-1])
            event_id = parts[-1:]

    return {
        "sid": service_key,
        "eid": eid if raw_eid else event_id
    }


def nowString():
    s = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " "
    return s


if __name__ == '__main__':
    pass
