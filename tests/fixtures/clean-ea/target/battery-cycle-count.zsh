#!/bin/zsh --no-rcs
# Jamf Pro Extension Attribute: reports the battery cycle count.
# Read-only. Prints exactly one <result> on every path.

export PATH=/usr/bin:/bin:/usr/sbin:/sbin

if ! output=$(/usr/sbin/ioreg -r -c AppleSmartBattery); then
  echo "<result>Error: ioreg failed</result>"
  exit 0
fi

if [[ "$output" != *AppleSmartBattery* ]]; then
  echo "<result>No battery</result>"
  exit 0
fi

cycles=$(print -r -- "$output" | /usr/bin/awk -F' = ' '/"CycleCount" =/ { print $2; exit }')

if [[ "$cycles" == <-> ]]; then
  echo "<result>${cycles}</result>"
else
  echo "<result>Error: no cycle count</result>"
fi
exit 0
