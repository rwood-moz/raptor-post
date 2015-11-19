#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys, os

sources = '../sources.xml'
gecko_tag = '<project name="https://hg.mozilla.org/integration/b2g-inbound" path="gecko" remote="hgmozillaorg" revision='
gecko = 'n/a'

def getGecko():
  try:
    f = open(sources, 'r')

    for line in f:
      if line.find(gecko_tag) != -1:
        offset = line.find("revision") + 10
        gecko = line[offset:offset+12]
        print('Found gecko revision from %s: %s' %(sources, gecko))

    if gecko == 'n/a':
      print('Gecko rev not found in %s' % sources)
      sys.exit(-1)

  except:
    print('Unable to get geck rev')
    sys.exit(-1)

  return gecko
