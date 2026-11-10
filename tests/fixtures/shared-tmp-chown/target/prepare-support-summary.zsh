#!/bin/zsh --no-rcs
# Jamf Pro policy script (runs as root): writes a short support summary that the
# signed-in user can open and send to the help desk.

export PATH=/usr/bin:/bin:/usr/sbin:/sbin
summary="/tmp/support-summary.txt"

console_user=$(/usr/bin/stat -f%Su /dev/console)
if [[ -z "$console_user" || "$console_user" == "root" || "$console_user" == "loginwindow" ]]; then
  echo "No console user; nothing to do"
  exit 0
fi

{
  echo "Computer: $(/usr/sbin/scutil --get ComputerName)"
  echo "macOS: $(/usr/bin/sw_vers -productVersion)"
  echo "Generated: $(/bin/date)"
} > "$summary" || exit 1

/usr/sbin/chown "$console_user" "$summary" || exit 1
/bin/chmod 600 "$summary" || exit 1
echo "Wrote $summary for $console_user"
