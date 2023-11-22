from sys import exc_info
from flask import Flask, g

# import Flask-APScheduler
from flask_apscheduler import APScheduler
import apscheduler.events
import apscheduler
import apscheduler.schedulers.asyncio
import flask_apscheduler

import logging
import structlog
import sys
import datetime

# logging.basicConfig()
# from structlog.stdlib import LoggerFactory
# structlog.configure(logger_factory=LoggerFactory())  

log = structlog.get_logger()
log.info("web server started")


# set configuration values
class Config(object):
    SCHEDULER_API_ENABLED = False


# create app
app = Flask(__name__)
app.config.from_object(Config())

# initialize scheduler
scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
# scheduler.api_enabled = True
# scheduler.init_app(app)

import os


@scheduler.task(trigger='interval', seconds=30, max_instances=1)
def run_bot():
    try:
        log.info('starting bot')
        os.system('python bot.py')
    except Exception as e:
        log.error('bot crash', exc_info=e)


def scheduler_event_listener(event: apscheduler.events.JobExecutionEvent):
    if event.exception:
        log.error('The job crashed', exc_info=event.exception)


scheduler.add_listener(scheduler_event_listener,
                       apscheduler.events.EVENT_JOB_EXECUTED | apscheduler.events.EVENT_JOB_ERROR)

log.info('jobs added', count=len(scheduler.get_jobs()))


@app.route('/')
def root():
    return "OK"


@app.route('/jobs')
def get_jobs():
    job_info = {
        "count": len(scheduler.get_jobs())
    }
    for job in scheduler.get_jobs():
        d = {
            "pending": job.pending,
            "id": job.id,
            "next_run_time": str(job.next_run_time)
        }
        job_info[job.id] = d
    return job_info


log.info('app configured')

log.info('starting scheduler')
scheduler.start()

if __name__ == '__main__':
    logging.basicConfig(
        format="%(message)s", stream=sys.stdout, level=logging.INFO
    )
    structlog.configure(
        processors=[
            structlog.threadlocal.merge_threadlocal,  # <--!!!
            structlog.processors.KeyValueRenderer(
                key_order=["event", "view", "peer"]
            ),
        ],
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    app.run()
