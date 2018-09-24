import time
def listToStringParser(lst, seperator=','):
    return ("%s" % seperator).join(lst)

def stringToListParser(string, seperator=','):
    return string.split(seperator)

def timeInMs():
    return int(time.time() * 100)