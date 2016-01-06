#!/bin/bash -x

# verify all coldlaunch tests finished, via the existence 
# of a {APP_ORITIN}{ENTRYPOINT}_retval.txt file

listOfFiles=( 
  "calendar_retval.txt"
  "camera_retval.txt"
  "clock_retval.txt"
  "communications-contacts_retval.txt"
  "communications-dialer_retval.txt"
  "email_retval.txt"
  "fm_retval.txt"
  "ftu_retval.txt"
  "gallery_retval.txt"
  "music_retval.txt"
  "settings_retval.txt"
  "sms_retval.txt"
  "video_retval.txt"
  "test-startup-limit_retval.txt" )

for nextFile in "${listOfFiles[@]}"
do
  if [ -f "$nextFile" ]
  then
    echo 'Found' $nextFile
  else
    echo 'Return value not found:' $nextFile
    exit 1
  fi
done

exit 0
