import asyncio
import aiohttp
import json
import sys

class GetScriptError(Exception):
    pass

class HttpClientAsync:
    def __init__(self, host, port):
        self.url = f'http://{host}:{port}'

    def __call__(self, tables, sqlQueryObjs):
        return asyncio.run(self.main(tables, sqlQueryObjs))

    async def main(self, tables, sqlQueryObjs):
        async with aiohttp.ClientSession() as session:
            cmd = await self.getTables(session, tables)
            scripts = await self.getScripts(session, sqlQueryObjs)
            if any(scripts):
                return cmd, list(filter(lambda v: v is not None, scripts))
            else: 
                raise GetScriptError

    async def getTables(self, session, tables):
        url = self.url + '/tables1'
        cmd = await self.fetchData(session, url, json.dumps(list(tables)))
        return cmd if cmd else None

    async def getScripts(self, session, sqlObjs):
        url=self.url + '/script'
        scripts = []
        for sqlObj in sqlObjs:
            sqlObjJson = json.dumps(sqlObj.to_json())
            script = await self.fetchData(session, url, sqlObjJson)
            scripts.append(script if script else None)
        return scripts

    async def fetchData(self, session, url, data):
        try:
            async with session.post(url, json=data) as resp:
                if resp.status == 200:
                    payload = await resp.json()
                    return payload['data']
                elif resp.status == 503:
                    return await self.handleServerError(resp)
                else:
                    print(f'request to {resp.real_url} return {resp.status}: {resp.reason}')
                    return None
        except aiohttp.ClientConnectionError as e:
            print(f'ERROR: fail connected to {e.host}:{e.port}')
            sys.exit(0)
        except aiohttp.ClientResponseError as e:
            print(e)
            print(f'ERROR: handle response from server on {e.request_info.url} \
                [{e.message}]')
            sys.exit(0)
        except aiohttp.ClientError as e:
            print(f'Unexcepted error from get data from server: {e}')
            sys.exit(0)

    async def handleServerError(self, response):
        payload = await response.json()
        errorMessage = payload['error']
        print(f'request to {response.real_url} return {response.status}: {response.reason}, message: {errorMessage}')
        return None
