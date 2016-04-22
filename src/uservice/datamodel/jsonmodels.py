L2i = {
    "L2i": {
        "BLineOffset": [range(12)] * 4,
        "ChannelId": [range(639)] * 1,
        "FitsSpectrum": [range(639)] * 1,
        "FreqMode": 0,
        "FreqOffset": 0.0,
        "InvMode": "",
        "LOFreq": [range(12)] * 1,
        "MinLmFactor": 0,
        "PointOffset": 0.0,
        "Residual": 0.0,
        "STW": [range(1)] * 12,
        "ScanId": 0,
    }
}


def check_json(data, prototype={"Data": ""}):
    """Go through data, and try to add contents to prototype.

    Will fail if data contains unexpected contents."""
    lowKey = {}
    for k in prototype.keys():
        lowKey[k.lower] = k

    fixedData = {}
    for k in data.keys:
        try:
            fixedData[lowKey[k.lower]] = data[k]
        except KeyError:
            return {"JSONError:": "Data contains unexpected key '{0}'."
                    "".format(k)}

    for k in prototype.keys():
        try:
            fixedData[k]
        except KeyError:
            return {"JSONError:": "Data is missing expected key '{0}'."
                    "".format(k)}

    return fixedData
