#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

import tornado.ioloop
import tornado.web

from thumbor.handlers.blacklist import BlacklistHandler
from thumbor.handlers.core import CoreHandler
from thumbor.handlers.healthcheck import HealthcheckHandler
from thumbor.handlers.image_resource import ImageResourceHandler
from thumbor.handlers.imaging import ImagingHandler
from thumbor.handlers.upload import ImageUploadHandler
from thumbor.lifecycle import Events
from thumbor.url import Url


class ThumborServiceApp(tornado.web.Application):
    def __init__(self, context):
        self.context = context
        self.debug = getattr(self.context.server, "debug", False)
        self.data = {}
        super(ThumborServiceApp, self).__init__(self.get_handlers(), debug=self.debug)

        self.filters_map = []

        for filter_cls in self.context.modules.filters:
            self.filters_map.append(
                {
                    "regex": filter_cls.regex,
                    "parsers": filter_cls.parsers,
                    "method": filter_cls.runnable_method,
                    "instance": filter_cls(""),
                }
            )

    def get_handlers(self):
        handlers = [
            (r"/favicon.ico", tornado.web.ErrorHandler, {"status_code": 404}),
            (r"/healthcheck", HealthcheckHandler),
        ]

        Events.trigger_sync(Events.Server.before_app_handlers, self, handlers=handlers)

        if self.context.config.UPLOAD_ENABLED:
            # Handler to upload images (POST).
            handlers.append((r"/image", ImageUploadHandler, {"context": self.context}))

            # Handler to retrieve or modify existing images  (GET, PUT, DELETE)
            handlers.append(
                (r"/image/(.*)", ImageResourceHandler, {"context": self.context})
            )

        if self.context.config.USE_BLACKLIST:
            handlers.append(
                (r"/blacklist", BlacklistHandler, {"context": self.context})
            )

        handlers.append((Url.regex(), CoreHandler))

        # Imaging handler (GET)
        # handlers.append((Url.regex(), ImagingHandler, {"context": self.context}))

        Events.trigger_sync(Events.Server.after_app_handlers, self, handlers=handlers)

        return handlers
