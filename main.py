#!/usr/bin/python

NOAA_18 = 28654
NOAA_15 = 25338
NOAA_19 = 33591
METEOR_M2_2 = 44387
METEOR_M2 = 40069

SATS = {"noaa19": NOAA_19,
        "noaa18": NOAA_18,
        "noaa15": NOAA_15,
        "meteorm2-2": METEOR_M2_2,
        "meteorm2": METEOR_M2}

LAT = "56.026706451127"
LONG = "-5.7731581771188"
API_KEY = "E3VFDJ-UWRTXU-WX5PNC-4740"

import urllib.request
import io, json, datetime, sys, time, traceback, threading, argparse

def pad(string, spaces, char, end="end"):
    characters = char * (spaces - len(string))
    if end == "end":
        return string + characters
    elif end == "start":
        return characters + string
    else:
        raise Exception("IllegalArgumentException: Expected 'start' or 'end', got '{}'".format(end))

def get_datetime(number):
    time = datetime.datetime.fromtimestamp(number)
    minute = pad(str(time.minute), 2, "0", end="start")
    hour =   pad(str(time.hour), 2, "0", end="start")
    day =    pad(str(time.day), 2, "0", end="start")
    month =  pad(str(time.month), 2, "0", end="start")

    if int(day) == datetime.datetime.now().day:
        return "{}:{}, today".format(hour, minute)
    elif int(day) - 1 == datetime.datetime.now().day:
        return "{}:{}, tomorrow".format(hour, minute)
    else:
        return "{}:{}, {}/{}".format(hour, minute, day, month)

def getURL(SAT_ID, LAT, LONG, ALT, DAYS, MIN_PASS, API_KEY):
    return "https://www.n2yo.com/rest/v1/satellite/radiopasses/{sat_id}/{lat}/{long}/{alt}/{days}/{min_pass}/&apiKey={api_key}".format(
        sat_id = SAT_ID, lat = LAT, long = LONG, alt = ALT, days = DAYS, min_pass = MIN_PASS, api_key = API_KEY)
    
def get_data(sat, days, min_pass):
    url = getURL(SATS[sat], LAT, LONG, 0, days, min_pass, API_KEY)

    u = urllib.request.urlopen(url, data = None)
    f = io.TextIOWrapper(u,encoding='utf-8')
    text = f.read()
    
    data = json.loads(text)
    return data

def getLine(p,info):
    elevation = str(p["maxEl"])
    start_time = p["startUTC"]
    start_heading = str(p["startAzCompass"])
    mid_heading = str(p["maxAzCompass"])
    end_heading = str(p["endAzCompass"])

    
    return  pad(info["satname"], 12, " ") + "|" +\
            pad(get_datetime(start_time), 17, " ") + "|" +\
            pad(" " + elevation + "°", 15, " ") + "|" +\
            pad(" " + start_heading, 15, " ") + "|" +\
            pad(" " + mid_heading, 13, " ") + "|" +\
               " " + end_heading

def format_data(table):
    out = []
    out.append("Satellite   | Time            | Max elevation | Start heading | Mid heading | End heading")
    out.append("------------|-----------------|---------------|---------------|-------------|------------")
    if type(table) == list:
        n = []
        for t in table:
            for p in t["passes"]:
                n.append({**p, **{"info": t["info"]}})
        n.sort(key=lambda x: x["startUTC"])
        return "\n".join(
            [getLine(p, p["info"]) for p in n])
        
    else:
        for p in table["passes"]:
            out.append(getLine(p, table["info"]))
        return "\n".join(out)
    

def main():
    parser = argparse.ArgumentParser(description="Commandline interface to https://n2yo.com/")

    group = parser.add_mutually_exclusive_group(required=True)    
    group.add_argument("-s", "--satellite", nargs=1, type=str,
                        help="Satellite name.", choices=SATS.keys())
    
    parser.add_argument("-d", "--days", nargs=1, type=int, default=[5], help="Number of days to find predictions for. Default: 5")
    parser.add_argument("-a", "--angle", nargs=1,type=int, default=[40], help="Minimum elevation required. Default: 40")
    group.add_argument("-A", "--all-passes", required=False, action="store_true", help="Show all satellite passes")

    args = parser.parse_args()
    if args.all_passes:
        all_sats = []
        for k in SATS.keys():
            all_sats.append(get_data(k, args.days[0], args.angle[0]))
        print(format_data(all_sats))
    else:
        print(format_data(
              get_data(args.satellite[0], args.days[0], args.angle[0])
              ))

main()
