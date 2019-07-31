from webtest_sanic.app import WSGIHandler

__version__ = '0.2.0'

__all__ = ['TestApp']

import webtest
import sanic



class TestApp(webtest.TestApp):
    """A modified `webtest.TestApp` that can wrap an `sanic.app.Sanic`. Takes the same
    arguments as `webtest.TestApp`.
    """

    def __init__(self, app, *args, **kwargs):
        self.sanic_app = None
        # checking for the loop for Sanic
        if isinstance(app, sanic.app.Sanic):
            if 'loop' in kwargs:
                loop = kwargs.pop('loop')
            else:

                raise ValueError('Must provide a loop to TestApp')
            self.sanic_app = app = WSGIHandler(app, loop)
        super().__init__(app, *args, **kwargs)
