from aioredis import RedisError, Redis
import traceback
import logging


class TemplaterService:
    def __init__(self, redis):
        self.redis = RedisExecutor(redis)

    async def makeSqlQuery(self, sqlInit):
        sql = await self.initPartSqlObj(sqlInit)
        mainTable = sql['mainTable']
        tableName = sql['tableName']
        alias = sql['alias']
        filter = sql['filter']
        tables = sql['tables'].items()
        sqlScript = f'select * \nfrom {tableName} {alias} \n'

        for table, join in tables:
            try:
                sqlScript += await self.specifyQuery(mainTable, table, join)
            except TableNotFoundException:
                sqlScript += await self.speculateQuery(table, join, alias)
        return sqlScript + filter

    async def initPartSqlObj(self, sqlInit):
        sqlObj = sqlInit
        sqlObj['alias'] = await self.redis.getAlias(sqlInit['mainTable'])
        sqlObj['tableName'] = await self.redis.getTableName(sqlInit['mainTable'])
        return sqlObj

    async def specifyQuery(self, mainTable, table, join):
        sqlLine = await self.redis.specifyQuery(mainTable, table)
        return f'{join}{sqlLine}\n'

    async def speculateQuery(self, table, join, alias):
        sqlLine = await self.redis.speculateQuery(table)
        sqlText = (sqlLine).replace("{X}", alias)
        if len(sqlText) > 0:
            return f'{join}{sqlText}\n'
        else:
            return f'{join} {table} {table[:3].lower()} on {table[:3].lower()}. = {alias}.\n'

    async def makeSelectCmd(self, tables):
        selectCmds = []
        cmd = "select top 1 * from "
        for table in tables:
            tableName = await self.redis.getTableName(table)
            selectCmds.append(cmd + tableName + '\n')
        selectCmds.insert(0, '\n')
        selectCmds.append('----\n\n')
        return selectCmds


class TableNotFoundException(Exception):
    pass

class GetSqlExpressionError(Exception):
    pass


class RedisExecutor:
    def __init__(self, redis):
        self.redis = redis
        self.logger = logging.getLogger("server.app")

    async def getAlias(self, mainTable):
        result = await self.exec(f'care:{mainTable}')
        if result is None:
            self.logger.warning(f"Alias for table {mainTable} not found")
            return "a"
        return result

    async def getTableName(self, table):
        result = await self.exec(f'care:{table}:name')
        if result is None:
            self.logger.warning(f"Name for table {table} not found")
            return table
        return result

    async def specifyQuery(self, mainTable, table):
        result = await self.exec(f'care:{mainTable}:{table}')
        if result is None:
            raise TableNotFoundException
        return result

    async def speculateQuery(self, table):
        self.logger.warning(f'Use speculate query for table {table}')
        result = await self.exec(f'care:{table}:join')
        if result is None:
            self.logger.warning(
                f'Speculate query failed: Table {table} not found')
            return ""
        return result

    async def exec(self, cmd):
        try:
            return await self.redis.get(cmd)
        except RedisError as e:
            self.logger.error(e)
            raise GetSqlExpressionError
        except ConnectionRefusedError as e:
            self.logger.error(e)
            raise GetSqlExpressionError
        except Exception as e:
            self.logger.error(''.join(traceback.format_exception(
                etype=type(e), value=e, tb=e.__traceback__)))
            raise GetSqlExpressionError
