
import os
import subprocess
import sys
import logging

from flask import Flask, jsonify
from flask.logging import default_handler
from datafunctions.log.log import startLog, getLogFile


SCRAPER_NAME = './run_scrapers.py'
startLog(getLogFile(__file__))
APP_LOG = logging.getLogger('root')

APP_LOG.info('Creating app...')
application = Flask(__name__)
werkzeug_logger = logging.getLogger('werkzeug')
for handler in APP_LOG.handlers:
	werkzeug_logger.addHandler(handler)
	application.logger.addHandler(handler)


@application.route('/start')
def start():
	"""
	Starts the web scrapers.
	"""

	tries = 0
	result = {
		'running': False,
		'tries': 0,
		'message': 'Unknown failure.'
	}
	try:
		APP_LOG.info('/start called')
		max_tries = 5
		while not check_running(SCRAPER_NAME) and tries < max_tries:
			APP_LOG.info(f'Scraper not running, attempting to start it (try {tries + 1} of {max_tries})')
			with open(os.devnull, 'r+b', 0) as DEVNULL:
				subprocess.Popen(['nohup', sys.executable, SCRAPER_NAME],
					stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, close_fds=True, preexec_fn=os.setpgrp)
			tries += 1

		if check_running(SCRAPER_NAME):
			APP_LOG.info(f'Scraper running.')
			if tries == 0:
				result = {
					'running': True,
					'tries': tries,
					'message': f'{SCRAPER_NAME} already running.'
				}
			else:
				result = {
					'running': True,
					'tries': tries,
					'message': f'{SCRAPER_NAME} started after {tries} tries.'
				}
		else:
			result = {
				'running': False,
				'tries': tries,
				'message': f'Failed to start {SCRAPER_NAME} after {tries} tries.'
			}

		APP_LOG.info(f'result: {result}')

	except Exception as e:
		result = {
			'running': False,
			'tries': tries,
			'message': f'Aborting after {type(e)} exception on try {tries}: {e}'
		}
		APP_LOG.info(f'result: {result}')
		APP_LOG.info(e, exc_info=True)

	return jsonify(result)


def check_running(pname):
	APP_LOG.info(f'check_running called, pname: {pname}')
	result = os.system(f'ps -Af | grep -v grep | grep -v log | grep {pname}')
	APP_LOG.info(f'exit code: {result}')
	return result == 0


if __name__ == '__main__':
	APP_LOG.info('Starting Flask dev server...')
	application.run()
