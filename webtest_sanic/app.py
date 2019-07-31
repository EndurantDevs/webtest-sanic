"""
webtest-sanic provides integration of WebTest with Sanic applications

.. code-block:: python

    import asyncio

    from sanic import Sanic
    from sanic.response import json
    from webtest_sanic import TestApp

    app = Sanic()

    @app.route('/')
    async def test(request):
        return json({'hello': 'world'})

    loop = asyncio.new_event_loop()

    def test_hello():
        client = TestApp(app, loop=loop)
        res = client.get('/')
        assert res.status_code == 200
        assert res.json == {'message': 'Hello world'}
"""

import webob

from .utils import TestClient


def WSGIHandler(app, loop):
    """Return a wsgi application given an `sanic.app.Sanic`."""

    def handle(environ, start_response):
        #initializing of TestClient
        #it starts TestServer by itself
        client = TestClient(app)
        loop.run_until_complete(client.start_server())
        req = webob.Request(environ)
        #Using internal method of pytest-sanic.utils here
        #.utils.py in this project file is from that plugin
        coro = client._request(req.method, req.path,
            data=req.body,
            params=req.params,
            headers=dict(req.headers)
        )
        result = loop.run_until_complete(coro)
        body = loop.run_until_complete(result.read())
        raw_headers = list(result.raw_headers)
        headerlist = [(name.decode('latin1'), value.decode('latin1'))
                      for name, value in raw_headers]
        res = webob.Response(
            body=body,
            status=result.status,
            content_type=result.content_type,
            headerlist=headerlist,
            charset=result.charset
        )
        start_response(res.status, res.headerlist)
        loop.run_until_complete(client.close())
        return res.app_iter
    return handle
