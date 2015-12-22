#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Original source:
# https://github.com/mozilla/mozmill-ci/blob/master/jenkins-master/jobs/scripts/workspace/submission.py

import argparse
import os
import re
import socket
import time
from urlparse import urljoin, urlparse
import uuid

from config import config
from lib import utils

import logging
logging.basicConfig()

here = os.path.dirname(os.path.abspath(__file__))

RESULTSET_FRAGMENT = 'api/project/{repository}/resultset/?revision={revision}'
JOB_FRAGMENT = '/#/jobs?repo={repository}&revision={revision}'

BUILD_STATES = ['running', 'completed']

RESULT_MARKER = 'visuallyLoaded'
ONE_DAY_MS = 86400000

class RaptorResultParser(object):

    BUSTED = 'busted'
    SUCCESS = 'success'
    TESTFAILED = 'testfailed'
    UNKNOWN = 'unknown'

    def __init__(self, retval, log_file, threshold):
        self.retval = retval
        self.log_file = log_file
        self.failure_re = re.compile(r'Aborted due to error')
        self.results_re = re.compile(r'^\| %s        \| \d' % RESULT_MARKER)
        self.threshold = float(threshold)
        self.failures = []
        self.result_line = []
        self.parse_results()

    def parse_results(self):
        # search the console log for raptor aborted error, if errors, mark as busted
        try:
            with open(self.log_file, 'r') as f:
                for line in f.readlines():
                    if self.failure_re.search(line):
                        self.failures.append(line)
        except IOError:
            print('Cannot look for failures due to missing log file: {}'.format(self.log_file))
            self.retval = 1

        if self.retval == 1 or self.failures:
            return

        # raptor not aborted, so check actual result value
        try:
            with open(self.log_file, 'r') as f:
                for line in f.readlines():
                    if self.results_re.match(line):
                        self.result_line.append(line)

        except IOError:
            print('Raptor "visuallyLoaded" results not found in log file: {}'.format(self.log_file))
            self.retval = 1

        if not self.result_line or len(self.result_line) > 1: 
            self.retval = 1
        else:
            print('Found result line for %s:' % RESULT_MARKER)
            print self.result_line
            x = self.result_line[0].split('|')

            if len(x) != 9:
                print("Unable to find a '95% Bound' value for " + RESULT_MARKER)
                self.retval = 1
            else:
                # want value in '95% Bound' column which is the last value in the row
                result = float(x[7].strip())
                print('%s: %.2f' % (RESULT_MARKER, result))
                print('Acceptable max: %.2f' % self.threshold)

                # compare with provided acceptable threshold
                if result <= self.threshold:
                    print('Result: PASS')
                else:
                    print('Result: FAIL')
                    self.failures.append('Coldlaunch result exceeds the allowed threshold')

    @property
    def status(self):
        status = self.UNKNOWN

        # retval.txt was not written - so most likely an abort
        if self.retval is None or (self.retval and not self.failures):
            status = self.BUSTED

        elif not self.failures:
            status = self.SUCCESS

        elif self.failures:
            status = self.TESTFAILED

        return status

    def failures_as_json(self):
        failures = {'all_errors': [], 'errors_truncated': True}

        for failure in self.failures:
            failures['all_errors'].append({'line': failure, 'linenumber': 1})

        return failures


class Submission(object):

    def __init__(self, repository, settings, app_name, test_type,
                 treeherder_url=None, treeherder_client_id=None, treeherder_secret=None):

        self.repository = repository
        self.revision = utils.getGecko()
        self.device = (os.environ['DEVICE_TYPE']).strip().lower()
        self.memory = (os.environ['MEMORY']).strip()
        self.app_name = app_name
        self.test_type = test_type
        self.settings = settings

        self._job_details = []

        self.url = treeherder_url
        self.client_id = treeherder_client_id
        self.secret = treeherder_secret

        if not self.client_id or not self.secret:
            raise ValueError('The client_id and secret for Treeherder must be set.')

    def _get_treeherder_platform(self):
        platform = None

        info = mozinfo.info

        if info['os'] == 'linux':
            platform = ('linux', '%s%s' % (info['os'], info['bits']), '%s' % info['processor'])

        elif info['os'] == 'mac':
            platform = ('mac', 'osx-%s' % info['os_version'].replace('.', '-'), info['processor'])

        elif info['os'] == 'win':
            versions = {'5.1': 'xp', '6.1': '7', '6.2': '8'}
            bits = ('-%s' % info['bits']) if info['os_version'] != '5.1' else ''
            platform = ('win', 'windows%s%s' % (versions[info['os_version']], '%s' % bits),
                        info['processor'],
                        )

        return platform

    def create_job(self, guid, **kwargs):
        job = TreeherderJob()

        job.add_job_guid(guid)

        job.add_product_name('raptor')

        job.add_project(self.repository)
        job.add_revision_hash(self.retrieve_revision_hash())

        # Add platform and build information
        job.add_machine(socket.getfqdn())
        platform = ("", "B2G Raptor %s %s" % (self.device, self.memory), "")
        job.add_machine_info(*platform)
        job.add_build_info(*platform)

        # TODO debug or others?
        job.add_option_collection({'opt': True})

        # TODO: Add e10s group once we run those tests
        job.add_group_name(self.settings['treeherder']['group_name'].format(**kwargs))
        job.add_group_symbol(self.settings['treeherder']['group_symbol'].format(**kwargs))

        # Bug 1174973 - for now we need unique job names even in different groups
        job.add_job_name(self.settings['treeherder']['job_name'].format(**kwargs))
        job.add_job_symbol(self.settings['treeherder']['job_symbol'][self.app_name].format(**kwargs))

        # request time will be the jenkins TEST_TIME i.e. when jenkins job started
        job.add_submit_timestamp(int(os.environ['TEST_TIME']))

        # test start time for that paraticular app is set in jenkins job itself
        job.add_start_timestamp(int(os.environ['RAPTOR_APP_TEST_TIME']))

        # Bug 1175559 - Workaround for HTTP Error
        job.add_end_timestamp(0)

        return job

    def retrieve_revision_hash(self):
        if not self.url:
            raise ValueError('URL for Treeherder is missing.')

        lookup_url = urljoin(self.url,
                             RESULTSET_FRAGMENT.format(repository=self.repository,
                                                       revision=self.revision))

        print('Getting revision hash from: {}'.format(lookup_url))
        response = requests.get(lookup_url)
        response.raise_for_status()

        if not response.json():
            raise ValueError('Unable to determine revision hash for {}. '
                             'Perhaps it has not been ingested by '
                             'Treeherder?'.format(self.revision))

        return response.json()['results'][0]['revision_hash']

    def submit(self, job, logs=None):
        logs = logs or []

        # We can only submit job info once, so it has to be done in completed
        if self._job_details:
            job.add_artifact('Job Info', 'json', {'job_details': self._job_details})

        job_collection = TreeherderJobCollection()
        job_collection.add(job)

        print('Sending results to Treeherder: {}'.format(job_collection.to_json()))
        url = urlparse(self.url)
       
        client = TreeherderClient(protocol=url.scheme, host=url.hostname,
                                  client_id=self.client_id, secret=self.secret)
        client.post_collection(self.repository, job_collection)

        print('Results are available to view at: {}'.format(
            urljoin(self.url,
                    JOB_FRAGMENT.format(repository=self.repository, revision=self.revision))))

    def submit_running_job(self, job):
        job.add_state('running')
        self.submit(job)

    def get_threshold(self):
        # get the acceptable maximum value for the corresponding test, & device (including memory)
        return self.settings['thresholds'][self.device][self.memory][self.app_name]

    def build_dashboard_url(self):
        # build raptor dashboard url for given device, branch, memory etc.
        # i.e. https://raptor.mozilla.org/dashboard/script/measures?var-device=flame-kk&var-memory=512&var-branch=master
            # &var-test=cold-launch&from=1448122404897&to=1448381604897&var-metric=All&var-aggregate=95%25%20Bound&panelId=3&fullscreen

        dash_pre = "https://raptor.mozilla.org/dashboard/script/measures?"
        dash_dev = "var-device=%s" % self.device.lower()
        dash_mem = "&var-memory=%s" % self.memory
        dash_branch = "&var-branch=master"
        dash_test = "&var-test=%s" % self.test_type

        test_time =  int(os.environ['TEST_TIME'])
        from_time = test_time - (ONE_DAY_MS * 2)
        to_time = test_time + (ONE_DAY_MS * 2)
        dash_from = "&from=%d" % from_time
        dash_to = "&to=%d" % to_time

        dash_metric = "&var-metric=All"
        dash_agg = "&var-aggretate=95%25%20Bound"
        dash_panel = "&panelId=%s&fullscreen" % self.settings['panel-ids'][self.app_name]

        dashboard_url = dash_pre + dash_dev + dash_mem + dash_branch + dash_test + dash_from + dash_to + dash_metric + dash_agg + dash_panel

        print('Raptor dashboard: %s' % dashboard_url)
        return dashboard_url

    def submit_completed_job(self, job, retval):
        """Update the status of a job to completed.
        """
        # Retrieve acceptable threshold
        self.threshold = self.get_threshold()

        # Parse results log
        parser = RaptorResultParser(retval, self.settings['logs'][self.app_name].format(**kwargs), 
            self.threshold)
        job.add_result(parser.status)

        # If the Jenkins BUILD_URL environment variable is present add it as artifact
        if os.environ.get('BUILD_URL'):
            self._job_details.append({
                'title': 'Inspect Jenkins Build (VPN required)',
                'value': os.environ['BUILD_URL'],
                'content_type': 'link',
                'url': os.environ['BUILD_URL']
            })

        # Add link to raptor dashboard showing the results
        dashboard_url = self.build_dashboard_url()
        self._job_details.append({
            'title': 'Raptor dashboard',
            'value': dashboard_url,
            'content_type': 'link',
            'url': dashboard_url
        })

        job.add_state('completed')
        job.add_end_timestamp(int(time.time()))

        self.submit(job)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-name',
                        required=True,
                        help='The app name i.e. "Clock"')
    parser.add_argument('--test-type',
                        choices=config['test_types'].keys(),
                        required=True,
                        help='The name of the Raptor test for building the job name.')
    parser.add_argument('--repository',
                        required=True,
                        help='The repository name the build was created from.')
    parser.add_argument('--build-state',
                        choices=BUILD_STATES,
                        required=True,
                        help='The state of the build')
    #parser.add_argument('venv_path',
    #                    help='Path to the virtual environment to use.')

    aws_group = parser.add_argument_group('AWS', 'Arguments for Amazon S3')
    aws_group.add_argument('--aws-bucket',
                           default=os.environ.get('AWS_BUCKET'),
                           help='The S3 bucket name.')
    aws_group.add_argument('--aws-key',
                           default=os.environ.get('AWS_ACCESS_KEY_ID'),
                           help='Access key for Amazon S3.')
    aws_group.add_argument('--aws-secret',
                           default=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                           help='Access secret for Amazon S3.')

    treeherder_group = parser.add_argument_group('treeherder', 'Arguments for Treeherder')
    treeherder_group.add_argument('--treeherder-url',
                                  default=os.environ.get('TREEHERDER_URL'),
                                  help='URL to the Treeherder server.')
    treeherder_group.add_argument('--treeherder-client-id',
                                  default=os.environ.get('RAPTOR_TREEHERDER_CLIENT_ID'),
                                  help='Client ID for submission to Treeherder.')
    treeherder_group.add_argument('--treeherder-secret',
                                  default=os.environ.get('RAPTOR_TREEHERDER_SECRET'),
                                  help='Secret for submission to Treeherder.')

    return vars(parser.parse_args())


if __name__ == '__main__':
    print('Raptor Treeherder Submission Script Version %s' % config['version'])
    kwargs = parse_args()

    # Activate the environment, and create if necessary
    #from lib import environment
    #if environment.exists(kwargs['venv_path']):
    #    environment.activate(kwargs['venv_path'])
    #else:
    #    environment.create(kwargs['venv_path'], os.path.join(here, 'requirements.txt'))

    # Can only be imported after the environment has been activated
    import mozinfo
    import requests

    from thclient import TreeherderClient, TreeherderJob, TreeherderJobCollection

    settings = config['test_types'][kwargs['test_type']]
    th = Submission(kwargs['repository'],
                    treeherder_url=kwargs['treeherder_url'],
                    treeherder_client_id=kwargs['treeherder_client_id'],
                    treeherder_secret=kwargs['treeherder_secret'],
                    settings=settings,
                    app_name=kwargs['app_name'],
                    test_type=kwargs['test_type'])

    # State 'running'
    if kwargs['build_state'] == BUILD_STATES[0]:
        job_guid = str(uuid.uuid4())
        job = th.create_job(job_guid, **kwargs)
        th.submit_running_job(job)
        with file('job_guid.txt', 'w') as f:
            f.write(job_guid)

    # State 'completed'
    elif kwargs['build_state'] == BUILD_STATES[1]:
        # Read in job guid to update the report
        try:
            with file('job_guid.txt', 'r') as f:
                job_guid = f.read()
        except:
            job_guid = str(uuid.uuid4())

        # Read return value of the test script
        try:
            if kwargs['app_name'] == "contacts" or kwargs['app_name' == 'dialer']:
                retvalfile = "communications=" + kwargs['app_name'] + '_retval.txt'
            else:
                retvalfile = kwargs['app_name'] + '_retval.txt'

            #with file('../retval.txt', 'r') as f:
            with file(retvalfile, 'r') as f:
                retval = int(f.read())
        except IOError:
            retval = None

        job = th.create_job(job_guid, **kwargs)

        th.submit_completed_job(job, retval)
