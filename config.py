# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Original source:
# https://github.com/mozilla/mozmill-ci/blob/master/jenkins-master/jobs/scripts/workspace/config.py

import os

here = os.path.dirname(os.path.abspath(__file__))


config = {
    'version': '1.0.0',
    'test_types': {
        'cold-launch': {
            'treeherder': {
                'group_name': 'Raptor Performance',
                'group_symbol': 'Coldlaunch',
                'job_name': 'Coldlaunch ({app_name})',
                'job_symbol': {
                    "calendar": "cal",
                    "camera": "cam",
                    "clock": "clk",
                    "contacts": "con",
                    "dialer": "dlr",
                    "email": "eml",
                    "fm": "fm",
                    "ftu": "ftu",
                    "gallery": "gal",
                    "music": "mus",
                    "settings": "set",
                    "sms": "sms",
                    "test-startup-limit": "tst",
                    "video": "vid"
                },
            },
            'logs': {
                "calendar": os.path.join(here, '../calendar.log'),
                "camera": os.path.join(here, '../camera.log'),
                "clock": os.path.join(here, '../clock.log'),
                "contacts": os.path.join(here, '../communications-contacts.log'),
                "dialer": os.path.join(here, '../communications-dialer.log'),
                "email": os.path.join(here, '../email.log'),
                "fm": os.path.join(here, '../fm.log'),
                "ftu": os.path.join(here, '../ftu.log'),
                "gallery": os.path.join(here, '../gallery.log'),
                "music": os.path.join(here, '../music.log'),
                "settings": os.path.join(here, '../settings.log'),
                "sms": os.path.join(here, '../sms.log'),
                "test-startup-limit": os.path.join(here, '../test-startup-limit.log'),
                "video": os.path.join(here, '../video.log')
            },
            "thresholds": {
                "flame-kk" : {
                    "512": {
                        "calendar": 1792,
                        "camera": 1514,
                        "clock": 1299,
                        "contacts": 1033,
                        "dialer": 951,
                        "email": 730,
                        "fm": 783,
                        "ftu": 3638,
                        "gallery": 1122,
                        "music": 1166,
                        "settings": 2522,
                        "sms": 1429,
                        "test-startup-limit": 761,
                        "video": 1040
                    },
                    "1024": {
                        "calendar": 1777,
                        "camera": 1548,
                        "clock": 1292,
                        "contacts": 1033,
                        "dialer": 928,
                        "email": 727,
                        "fm": 770,
                        "ftu": 3602,
                        "gallery": 1133,
                        "music": 1150,
                        "settings": 2599,
                        "sms": 1420,
                        "test-startup-limit": 750,
                        "video": 1047
                    },
                },
                "aries": {
                    "2048": {
                        "calendar": 1018,
                        "camera": 916,
                        "clock": 711,
                        "contacts": 550,
                        "dialer": 520,
                        "email": 407,
                        "fm": 438,
                        "ftu": 2501,
                        "gallery": 582,
                        "music": 657,
                        "settings": 1685,
                        "sms": 796,
                        "test-startup-limit": 382,
                        "video": 622
                    },
                },
            },
            "panel-ids": {
                "calendar": 1,
                "camera": 2,
                "clock": 3,
                "contacts": 4,
                "dialer": 5,
                "email": 6,
                "fm": 7,
                "ftu": 14,
                "gallery": 8,
                "music": 10,
                "settings": 11,
                "sms": 9,
                "test-startup-limit": 13,
                "video": 12
            },
        },
    },
}
