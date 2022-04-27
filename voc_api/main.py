#!/usr/bin/env python3
import argparse
import logging
import os
from datetime import datetime

import pytz
import toml
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import voc_api.deps as deps
import voc_api.lib_misc as lm
# from voc_api.models import something

from .deps import logger
from .lib_cfg import config
from .routers import voc

# ################################################### SETUP AND ARGUMENT PARSING
# ##############################################################################
dir_path = os.path.dirname(os.path.realpath(__file__))


VERSION = 9
START_TIME = datetime.now(pytz.utc)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

tags_metadata = [
]

# ############################################ SERVER ROUTES
# #############################################################################


app = FastAPI(root_path=config.key('proxy_prefix'), openapi_tags=tags_metadata)

# Include sub routes
app.include_router(voc.router)

# Server config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # Build whoosh index
    deps.WH_INDEX = deps.init_state()


# ############################################################### SERVER ROUTES
# #############################################################################


@app.get("/")
def root():
    return lm.status_get(START_TIME, VERSION)


# ##################################################################### STARTUP
# #############################################################################
def main():
    parser = argparse.ArgumentParser(description='Matching server process')
    parser.add_argument('--config', dest='config', help='config file', default=None)
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Debug mode')
    args = parser.parse_args()

    # XXX: Lambda is a hack : toml expects a callable
    if args.config:
        t_config = toml.load(['config_default.toml', args.config])
    else:
        t_config = toml.load('config_default.toml')

    config.merge(t_config)

    if args.debug:
        logger.setLevel(logging.getLevelName('DEBUG'))
        logger.debug('Debug activated')
        config.set('log_level', 'debug')
        config.set(['server', 'log_level'], 'debug')
        logger.debug('Arguments: %s', args)
        config.dump(logger)
        logger.debug('config: %s', toml.dumps(config._config))

        uvicorn.run(
            "voc_api.main:app",
            reload=True,
            **config.key('server')
        )
    uvicorn.run(
        app,
        **config.key('server')
    )


if __name__ == "__main__":
    main()
