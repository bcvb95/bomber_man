import time
from datetime import datetime
import math
import requests
import netifaces as ni



def listToStringParser(lst, seperator=','):
    if len(lst) == 0:
        return ""
    return ("%s" % seperator).join(lst) 

def stringToListParser(string, seperator=','):
    if len(string) == 0:
        return []
    return string.split(seperator)

def recentMovesToStringParser(recent_moves, seperator=','):
    moves = [m[0] for m in recent_moves]
    return ("%s" % seperator).join(moves)

def timeInMs():
    now = datetime.now()
    return (now.second*1000000) + now.microsecond

def get_dist(p1,p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def getMyIP():
    net_intf = ni.interfaces()[ni.AF_INET]
    ni.ifaddresses(net_intf)
    ip = ni.ifaddresses(net_intf)[ni.AF_INET][0]['addr']
    return ip
