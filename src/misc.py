
def listToStringParser(lst, seperator=','):
    return ("%s" % seperator).join(lst) 

def stringToListParser(string, seperator=','):
    return string.split(seperator)