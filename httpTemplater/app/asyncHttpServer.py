import json
import aioredis
import sys
import yaml
import logging
import logging.config
import asyncio
import traceback
import os

from aioredis import RedisError
from aiohttp import web

from config import get_config, config_logging
from httpTemplater.app.TemplaterService import TemplaterService, RedisExecutor, GetSqlExpressionError


routes = web.RouteTableDef()

@routes.post('api/script')
async def makeSqlQuery(request):
    sqlExpression = await request.json()
    print(sqlExpression)
    status = 200
    try:
        sqlScript = await app['templater'].makeSqlQuery(sqlExpression)
        resp = {"data": sqlScript}
    except GetSqlExpressionError as e:
        status = 503
        resp = {"error": "sqlQuery not create"}
    return web.json_response(resp, status=status)


@routes.post('api/tables')
async def makeSelectCmd(request):
    tables = await request.json()
    status = 200
    try:
        cmds = await app['templater'].makeSelectCmd(json.loads(tables))
        resp = {"data": cmds}
    except GetSqlExpressionError as e:
        status = 503
        resp = {"error": "select commant not create"}

    return web.json_response(resp, status=status)


async def create_redis(app):
    app['redis'] = await aioredis.create_redis_pool(
        address=f"redis://{config['REDIS_ADDR']}:{config['REDIS_PORT']}",
        encoding='utf-8',
        minsize=5, maxsize=10,
        db=config['DB_NAME'],
        password=config['REDIS_PASS'])


async def close_redis(app):
    app['redis'].close()
    await app['redis'].wait_closed()


async def initTemplaretService(app):
    app['templater'] = TemplaterService(app['redis'])


async def on_prepare(req, resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
    resp.headers['Content-Type'] = 'application/json'

config = get_config()
config_logging()
appLogger = logging.getLogger("server.app")

app = web.Application()
app.add_routes(routes)
app.on_response_prepare.append(on_prepare)
app.on_startup.append(create_redis)
app.on_startup.append(initTemplaretService)
app.on_cleanup.append(close_redis)


try:
    port = 8080
    appLogger.info(f'Start server on port {port}')
    web.run_app(app, port=port, access_log_format='%a %t "%r" %s')
except RedisError as e:
    print(f'When creating a connection to the server \
          rised exception {e}')
    logging.getLogger("aiohttp.web").error(e)
except Exception as e:
    print(f'When starting server \
          an exception occurred {e}')
    logging.getLogger("aiohttp.web").error(
        ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)))
finally:
    appLogger.info('Server shutdown')
