"""
Original code from pytest-sanic. Please check NOTICE for more info.
Used for webtest integration without pytest-sanic dependency because of pytest plugin problems:
pytest-aiohttp and pytest-sanic
"""
from aiohttp import ClientSession, CookieJar
from sanic.server import serve, HttpProtocol
from inspect import isawaitable
from sanic.app import Sanic
import socket
import asyncio
import sys

HEAD = 'HEAD'
GET = 'GET'
DELETE = 'DELETE'
OPTIONS = 'OPTIONS'
PATCH = 'PATCH'
POST = 'POST'
PUT = 'PUT'


async def trigger_events(events, loop):
    """Trigger events (functions or async)

    :param events: one or more sync or async functions to execute
    :param loop: event loop
    """
    for event in events:
        result = event(loop)
        if isawaitable(result):
            await result


class TestServer:
    """
    a test server class designed for easy testing in Sanic-based Application.
    """

    def __init__(self, app, host='127.0.0.1',
                 loop=None, protocol=None,
                 backlog=100, ssl=None,
                 scheme=None, connections=None,
                 **kwargs):
        if not isinstance(app, Sanic):
            raise TypeError("app should be a Sanic application.")
        self.app = app
        self.loop = loop
        self.host = host
        self.protocol = protocol or HttpProtocol
        self.backlog = backlog
        self.server = None
        self.port = None
        self.connections = connections if connections else set()
        self.ssl = ssl
        if scheme is None:
            if self.ssl:
                self.scheme = "https"
            else:
                self.scheme = "http"
        else:
            self.scheme = scheme

        # Listeners
        self.before_server_start = None
        self.after_server_start = None
        self.before_server_stop = None
        self.after_server_stop = None

        # state
        self.closed = None
        self.is_running = False

    async def start_server(self, loop=None):
        if loop:
            self.loop = loop
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, 0))
        self.port = self.socket.getsockname()[1]

        # server settings
        server_settings = self.app._helper(
            host=self.host, port=self.port,
            ssl=self.ssl, sock=self.socket,
            loop=self.loop, protocol=self.protocol,
            backlog=self.backlog, run_async=True)

        # clean up host/port.
        # host/port should not be used.
        server_settings['host'] = None
        server_settings['port'] = None

        # Let's get listeners
        self.before_server_start = server_settings.get('before_start', [])
        self.after_server_start = server_settings.get('after_start', [])
        self.before_server_stop = server_settings.get('before_stop', [])
        self.after_server_stop = server_settings.get('after_stop', [])

        # Trigger before_start events
        await trigger_events(self.before_server_start, self.loop)

        # Connections
        server_settings["connections"] = self.connections

        # start server
        self.server = await serve(**server_settings)
        self.is_running = True
        self.app.is_running = True

        # Trigger after_start events
        await trigger_events(self.after_server_start, self.loop)

    async def close(self):
        """
        Close server.
        """
        if self.is_running and not self.closed:
            # Trigger before_stop events
            await trigger_events(self.before_server_stop, self.loop)

            # Stop Server
            self.server.close()
            await self.server.wait_closed()

            for connection in self.connections:
                connection.close_if_idle()

            # Force close connections
            coros = []
            for conn in self.connections:
                if hasattr(conn, "websocket") and conn.websocket:
                    coros.append(conn.websocket.close_connection())
                else:
                    conn.close()
            if (sys.version_info[0] == 3) and (sys.version_info[1] < 8):
                await asyncio.gather(*coros, loop=self.loop)
            else:
                await asyncio.gather(*coros)

            # Trigger after_stop events
            await trigger_events(self.after_server_stop, self.loop)

            self.closed = True
            self.is_running = False
            self.app.is_running = False
            self.port = None

    def has_started(self):
        """
        Check if server has started.
        """
        return self.server is not None

    def make_url(self, uri):
        return "{scheme}://{host}:{port}{uri}".format(
            scheme=self.scheme,
            host=self.host,
            port=self.port,
            uri=uri
        )


class TestClient:
    """
    a test client class designed for easy testing in Sanic-based Application.
    """

    def __init__(self, app, loop=None,
                 host='127.0.0.1',
                 protocol=None,
                 ssl=None,
                 scheme=None,
                 **kwargs):
        if not isinstance(app, Sanic):
            raise TypeError("app should be a Sanic application.")
        self._app = app
        self._loop = asyncio.get_event_loop()
        # we should use '127.0.0.1' in most cases.
        self._host = host
        self._ssl = ssl
        self._scheme = scheme
        self._protocol = HttpProtocol if protocol is None else protocol
        self._closed = False
        self._server = TestServer(
            self._app, loop=self._loop,
            protocol=self._protocol, ssl=self._ssl,
            scheme=self._scheme)
        self._responses = []
        self._websockets = []

    @property
    def app(self):
        return self._app

    @property
    def host(self):
        return self._server.host

    @property
    def port(self):
        return self._server.port

    @property
    def server(self):
        return self._server

    # @property
    # def session(self):
    #     return self._session

    def make_url(self, uri):
        return self._server.make_url(uri)

    async def start_server(self):
        """
        Start a TestServer that running Sanic application.
        """
        await self._server.start_server(loop=self._loop)

    async def close(self):
        """
        Close TestClient obj, and cleanup all fixtures created by test client.
        """
        if not self._closed:
            for resp in self._responses:
                resp.close()
            for ws in self._websockets:
                await ws.close()
            #await self._session.close()
            await self._server.close()
            self._closed = True

    async def _request(self, method, uri, *args, **kwargs):
        url = self._server.make_url(uri)
        cookie_jar = CookieJar(unsafe=True, loop=self._loop)
        async with ClientSession(loop=asyncio.get_event_loop(), cookie_jar=cookie_jar) as session:
            response = await session.request(
                method, url, *args, **kwargs
            )
            self._responses.append(response)
            return response

    async def get(self, uri, *args, **kwargs):
        return await self._request(GET, uri, *args, **kwargs)

    async def post(self, uri, *args, **kwargs):
        return await self._request(POST, uri, *args, **kwargs)

    async def put(self, uri, *args, **kwargs):
        return await self._request(PUT, uri, *args, **kwargs)

    async def delete(self, uri, *args, **kwargs):
        return await self._request(DELETE, uri, *args, **kwargs)

    async def patch(self, uri, *args, **kwargs):
        return await self._request(PATCH, uri, *args, **kwargs)

    async def options(self, uri, *args, **kwargs):
        return await self._request(OPTIONS, uri, *args, **kwargs)

    async def head(self, uri, *args, **kwargs):
        return await self._request(HEAD, uri, *args, **kwargs)

    async def ws_connect(self, uri, *args, **kwargs):
        """
        Create a websocket connection.

        a thin wrapper around aiohttp.ClientSession.ws_connect.
        """
        url = self._server.make_url(uri)
        cookie_jar = CookieJar(unsafe=True, loop=self._loop)
        async with ClientSession(loop=asyncio.get_event_loop(), cookie_jar=cookie_jar) as session:
            ws_conn = await session.ws_connect(
                url, *args, **kwargs
            )
            # Save it, clean up later.
            self._websockets.append(ws_conn)
            return ws_conn

    # Context Manager
    async def __aenter__(self):
        await self.start_server()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
