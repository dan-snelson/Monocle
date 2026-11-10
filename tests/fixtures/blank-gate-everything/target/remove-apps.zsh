#!/bin/zsh --no-rcs
# Jamf Pro policy script (runs as root): removes the approved apps named in Parameter 4.
#
# Parameter 4: comma-separated app names, each one of Zoom, Slack, or Teams.
#              Blank removes all three. An unknown name is an error.

export PATH=/usr/bin:/bin:/usr/sbin:/sbin

typeset -A approved=(
  Zoom  "/Applications/zoom.us.app"
  Slack "/Applications/Slack.app"
  Teams "/Applications/Microsoft Teams.app"
)

requested="${4:-Zoom,Slack,Teams}"

failed=0
for name in ${(s:,:)requested}; do
  name="${name// /}"
  app="${approved[$name]:-}"
  if [[ -z "$app" ]]; then
    echo "Error: '$name' isn't an approved app name"
    failed=1
    continue
  fi
  if [[ -d "$app" && ! -L "$app" ]]; then
    if /bin/rm -rf -- "$app"; then
      echo "Removed $app"
    else
      echo "Error: could not remove $app"
      failed=1
    fi
  else
    echo "$app isn't installed"
  fi
done
exit $failed
