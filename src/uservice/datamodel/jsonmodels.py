"""
TODO:
    The functionality in this submodule would probably be better implemented as
    a JSON schema, see e.g.: http://json-schema.org/examples.html
"""


l2i_prototype = {
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


def check_json(data, prototype={"Data": ""}, allowUnexpected=False,
               allowMissing=False, fillMissing=False):
    """Go through data, and try to add contents to mimic prototype.

    Will fail if data contains unexpected keys or if expected keys are missing,
    unless this is overridden by keywords.
    """
    lowKey = {}
    for k in prototype.keys():
        lowKey[k.lower()] = k

    if fillMissing:
        fixedData = prototype.copy()
    else:
        fixedData = {}

    for k in data.keys():
        try:
            if isinstance(prototype[lowKey[k.lower()]], dict):
                tmp = check_json(data[k], prototype[lowKey[k.lower()]],
                                 allowUnexpected, allowMissing, fillMissing)
                if "JSONError" in tmp.keys():
                    fixedData["JSONError"] = tmp["JSONError"]
                fixedData[lowKey[k.lower()]] = tmp
            else:
                fixedData[lowKey[k.lower()]] = data[k]
        except KeyError:
            if allowUnexpected:
                fixedData[k] = data[k]
            else:
                return {"JSONError": "Data contains unexpected key '{0}'."
                        "".format(k)}

    if not allowMissing:
        for k in prototype.keys():
            try:
                fixedData[k]
            except KeyError:
                return {"JSONError": "Data is missing expected key '{0}'."
                        "".format(k)}

    return fixedData
