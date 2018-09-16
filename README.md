# webtest-sanic
Integration of WebTest with [Sanic](https://github.com/huge-success/sanic) applications
Initially it was created to enable Sanic support in [Webargs](https://github.com/sloria/webargs) module

[![Build Status](https://img.shields.io/travis/EndurantDevs/webtest-sanic.svg?logo=travis)](https://travis-ci.org/EndurantDevs/webtest-sanic) [![Latest Version](https://pypip.in/version/webtest-sanic/badge.svg)](https://pypi.python.org/pypi/webtest-sanic/) [![Python Versions](https://img.shields.io/pypi/pyversions/webtest-sanic.svg)](https://github.com/EndurantDevs/webtest-sanic/blob/master/setup.py) [![Tests Coverage](https://img.shields.io/codecov/c/github/EndurantDevs/webtest-sanic/master.svg)](https://codecov.io/gh/EndurantDevs/webtest-sanic)

### Example Code ###

```python
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
```


### Installing

It is easy to do from `pip`

```
pip install webtest-sanic
```

or from sources

```
git clone git@github.com:EndurantDevs/webtest-sanic.git
cd webtest-sanic
python setup.py install
```

## Running the tests

To be sure everything is fine before installation from sources, just run:
```
python setup.py test
```
Or
```
pytest tests/
```

### Credits ###

This code is based on [webtest-aiohttp](https://github.com/sloria/webtest-aiohttp) by [Steven Loria](https://github.com/sloria) and [pytest-sanic](https://github.com/yunstanford/pytest-sanic) by [Yun Xu](https://github.com/yunstanford)
Please check [NOTICE](NOTICE.md) for more info.
