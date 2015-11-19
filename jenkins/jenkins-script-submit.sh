#!/bin/bash -x

RAPTOR_BUILD_STATE=$1
RAPTOR_TREEHERDER_APP_NAME=$2

python --version

source raptor-env/bin/activate

python --version

# when starting coldlaunch test, record start time for this app
if [[ "${RAPTOR_BUILD_STATE}" == "running" ]]; then
  export RAPTOR_APP_TEST_TIME=$(node -e "console.log(Date.now());")
fi

cd raptor-post
./submit-to-treeherder.py \
  --repository b2g-inbound \
  --build-state ${RAPTOR_BUILD_STATE} \
  --treeherder-url https://treeherder.allizom.org/ \
  --treeherder-client-id raptor \
  --treeherder-secret ${RAPTOR_TREEHERDER_SECRET} \
  --test-type cold-launch \
  --app-name ${RAPTOR_TREEHERDER_APP_NAME}

exit 0
