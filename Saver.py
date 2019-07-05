import os
import config


class FewLinesError(Exception):
    def __init__(self, fName, amountLines=0):
        self.fName = fName
        self.amountLines = amountLines

    def __str__(self):
        return f"FewLinesError: fName={self.fName},lines={self.amountLines}"


class Saver:
    def __init__(self):
        self.scriptPath = config.appConf['scriptPath']
        self.fAllScripts = config.appConf['fileAllScript']

    def save(self, fName):
        self.fName = fName
        for sqlFile in self.findSqlFile():
            try:
                lines = self.readSqlFile(sqlFile)
                formatLines = self.formatSqlFile(lines)
                self.saveSqlFile(formatLines)
            except FewLinesError as e:
                print(f'Error: Too few lines({e.args[1]}) in file {e.args[0]}')
            except FileNotFoundError as e:
                print(f'File {e.args[0]} not found')
            except IOError as e:
                print(f'Error:{e.strerror}: {e.filename}')
            except Exception as e:
                print(e)

    def findSqlFile(self):
        if self.fName != 'all':
            fNameSep = config.appConf['fileNameSep']
            if len(self.fName.split(fNameSep)) < 2:
                fName = self.fName
            else:
                fNameSep = " "
                fName = self.fName + ".sql"

        for root, _, files in os.walk(self.scriptPath):
            if self.fName != 'all':
                for file in files:
                    if fName == file.split(fNameSep)[0]:
                        self.fName = os.path.splitext(file)[0]
                        yield os.path.join(root, file)
                        return
            else:
                for file in files:
                    self.fName = os.path.splitext(file)[0]
                    yield os.path.join(root, file)
                return

    def readSqlFile(self, file):
        if file is None:
            raise FileNotFoundError(self.fName)
        if not os.path.exists(file):
            raise FileNotFoundError(self.fName)

        try:
            with open(file, 'r') as sqlFile:
                lines = sqlFile.readlines()
                try:
                    initLine = config.appConf['initLine']
                    startIdx = lines.index(initLine) + 1
                    return lines[startIdx:]
                except (ValueError, IndexError):
                    return lines
        except IOError:
            raise

    def formatSqlFile(self, lines):
        formatters = [HeadFormatter(self.fName), TailFormatter(self.fName)]
        for f in formatters:
            lines = f.format(lines)
        return lines

    def saveSqlFile(self, lines: list):
        try:
            with open(self.fAllScripts, 'a+') as fScripts:
                fScripts.writelines("".join(lines))
        except IOError:
            raise
   

class HeadFormatter:
    def __init__(self, fName):
        self.fName = fName

    def format(self, lines):
        if len(lines) == 0:
            raise FewLinesError(self.fName, len(lines))
        hStartSymbol = config.appConf['headerStartSymbol']
        hEndSymbol = config.appConf['headerEndSymbol']
        self.headerLine = f'{hStartSymbol}{self.fName}{hEndSymbol}'

        self.dropNewlineChar(lines, index=0)
        for index, line in enumerate(lines):
            if line[:len(hStartSymbol)] == hStartSymbol:
                return self.formatHeaderLine(lines, line, index)
        return self.linesWithHeader(lines)

    def formatHeaderLine(self, lines, line, index):
        amountLines = len(lines)
        # заголовок есть => количество строк должно быть больше 1
        if amountLines - index < 2:
            raise FewLinesError(self.fName, amountLines - index)
        if line == self.headerLine:
            return self.formatCorrectHeader(lines, index)
        else:
            return self.formatUnCorrectHeader(lines, index)

    def formatCorrectHeader(self, lines, index):
        lines = lines[index:]
        lines.insert(0, '\n')
        return lines

    def formatUnCorrectHeader(self, lines, index):
        lines = lines[index+1:]
        if len(lines) == 0:
            raise FewLinesError(self.fName, len(lines))
        lines.insert(0, f'{self.headerLine}')
        lines.insert(0, f'\n')
        return lines
    
    def linesWithHeader(self, lines):
        lines.insert(0, f'{self.headerLine}')
        lines.insert(0, f'\n')
        return lines
        
    def dropNewlineChar(self, lines, index):
        try:
            while lines[index] in ('\n', ' '):
                lines.pop(index)
            return lines
        except IndexError:
            raise FewLinesError(self.fName, 0)

class TailFormatter:
    def __init__(self, fName):
        self.fName = fName

    def format(self, lines):
        self.dropNewlineChar(lines)
        # т.к. заголовок c разделителем строки уже проставлен
        # количество строк должно быть болеше двух
        if len(lines) <= 2:
            raise FewLinesError(self.fName, len(lines))
        self.insertNewlineChar(lines)
        return self.linesWithScriptSep(lines)

    def insertNewlineChar(self, lines):
        lines.append('\n') if lines[-1][-1] == '\n' \
            else lines.append('\n\n')

    def linesWithScriptSep(self, lines):
        scriptSep = "--" * 40
        lines.append(scriptSep)
        return lines
    
    def dropNewlineChar(self, lines):
        try:
            while lines[-1] in ('\n', ' '):
                lines.pop()
            return lines
        except IndexError:
            raise FewLinesError(self.fName, 0)
