import os
import sys
import subprocess
from itertools import takewhile
from datetime import datetime

import config

class CreateFileError(Exception):
    pass

def fetchSqlScript(searchScript, fName):
    sqlScript = findSqlScript(searchScript)
    if sqlScript is None:
        raise FileNotFoundError
    
    try:
        sqlfName = createSqlFile(fName, sqlScript)
        return sqlfName
    except IOError:
        raise

def findSqlScript(searchScript):
    fAllScripts = config.appConf['fileAllScript']
    hStartSymbol = config.appConf['headerStartSymbol']
    hEndSymbol = config.appConf['headerEndSymbol']

    def fetchScript(line, file):
        return [line for line in
                    takewhile(lambda l: l[:5] != '----'
                          and l[:5] != hStartSymbol, fScripts)]

    if os.path.exists(fAllScripts):
        searchHeader = f'{hStartSymbol}{searchScript}{hEndSymbol}'
        with open(fAllScripts, "r") as fScripts:
            for line in fScripts:
                if line == searchHeader:
                    return fetchScript(line, fScripts)
    else:
        None

def createSqlFile(fName, sqlScript):
    scriptPath = config.appConf['scriptsPath']
    hStartSymbol = config.appConf['headerStartSymbol']
    hEndSymbol = config.appConf['headerEndSymbol']
    fNameSep = config.appConf['fileNameSep']

    fName = prepareFileName(fName, fNameSep)
    sqlfName = scriptPath + fName + '.sql'
    try:
        with open(sqlfName, 'w') as sqlFile:
            sqlFile.write(f'{hStartSymbol}{fName}{hEndSymbol}')
            sqlFile.writelines(sqlScript)
        return sqlfName
    except IOError:
        raise
        


def prepareFileName(fName, fNameSep):
    now = datetime.now()
    return fName if len(fName.split(fNameSep)) > 1 \
        else f"{fName}--{now.day}.{now.month}.{str(now.year)[-2:]}"


def openSqlFile(sqlFile):
    subprocess.Popen(["Ssms.exe", sqlFile, "-E",
                      "-S", "SERVER11", "-nosplash"])
    print('open Sql MS...')


