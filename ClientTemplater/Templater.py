import asyncio
import aiohttp
import json
import sys

import config

from ClientTemplater.HttpClientAsync import HttpClientAsync, GetScriptError
from funcUtil import createSqlFile


class Templater:
    def __init__(self, host, port, name):
        self.name = name
        self.httpClient = HttpClientAsync(host, port)

    def makeSqlScript(self, templates, globalFilter):
        tables, sqlObjs = self.formSqlObjs(templates, globalFilter)
        try:
            selectCmd, scripts = self.httpClient(tables, sqlObjs)
        except GetScriptError as e:
            print(f'Error make script: {e}')
            sys.exit(0)
        
        if selectCmd:
            sqlScript = selectCmd + scripts
        else: 
            sqlScript = scripts
        return createSqlFile(self.name, sqlScript)

    def formSqlObjs(self, templates, globalFilter):
        tables = set()
        sqlObjs = []
        for template in templates.split(';'):
            sqlItems = self.parseTemplate(template, globalFilter)
            tables.update(sqlItems.mainTable.split() + list(sqlItems.tables.keys()))
            sqlObjs.append(sqlItems)
        return tables, sqlObjs

    def parseTemplate(self, unit, globalFilter):
        body, join, filter = None, None, None
        template = unit.split("-")
        for item in template[1:]:
            param = item[0]
            if param == "t":
                body = item[2:].strip()
            if param == "j":
                join = item[2:].strip()
            if param == "f":
                filter = item[2:].strip()
        return SqlExpression(body, join, filter, globalFilter)


class SqlExpression:
    def __init__(self, body, join, filter, globalFilter):
        self._body = body
        self._join = join
        self._pfilter = filter
        self._globalFilter = globalFilter
        self.join = self.makeJoin()
        self.mainTable, self.tables = self.produceTables()

    def produceTables(self):
        resultTables = {}
        tables = self._body.split("+")
        mainTable = tables[0].strip()
        for table in tables[1:]:
            resultTables[table.strip()] = self.produceJoin(table)  # make dict
        return mainTable, resultTables

    def produceJoin(self, table):
        dropedTables = ['spAll', 'spV', 'all']
        if table in dropedTables:
            return ''
        else:
            return self.join

    def makeJoin(self):
        if self._join is None:
            return 'join '
        else:
            if 'join' in self._join:
                return self._join + ' '
            return self._join + ' join '

    @property
    def filter(self):
        finalFilter = "where "
        if self._pfilter is not None and self._globalFilter is not None:
            finalFilter += f'{self._pfilter}\nand {self._globalFilter}'
        elif self._pfilter is None and self._globalFilter is not None:
            finalFilter += self._globalFilter
        elif self._pfilter is not None and self._globalFilter is None:
            finalFilter += self._pfilter
        else:
            return '\n'
        return finalFilter + '\n' * 2

    def to_json(self):
        return {'mainTable': self.mainTable,
                'tables': self.tables,
                'filter': self.filter}

