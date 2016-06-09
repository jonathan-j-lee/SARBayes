"""
server
"""

from flask import Flask, g, render_template, jsonify
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

import database
from database.models import Subject, Group, Incident
from util import initialize_logging

app = Flask(__name__)


def database_initialized():
    return hasattr(g, 'engine') and hasattr(g, 'session')


def initialize_session(url='sqlite:///../data/isrid-master.db'):
    if not database_initialized():
        app.logger.info('Database initialized')
        g.engine, g.session = database.initialize(url)


@app.teardown_appcontext
def terminate_session(error):
    if database_initialized():
        app.logger.info('Database terminated')
        database.terminate(g.engine, g.session)


@app.route('/api/kaplan-meier', methods=['POST'])
def kaplan_meier():
    ...


@app.route('/')
def index():
    return render_template('index.html')


def execute(deploy=False, host='0.0.0.0', port=5000):
    initialize_logging('../logs/server.log', 'w+', app.logger)

    if deploy:
        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(port)
        IOLoop.instance().start()
    else:
        app.run(host, port, debug=True)


if __name__ == '__main__':
    execute()
