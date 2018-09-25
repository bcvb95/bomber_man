import time
from datetime import datetime

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
