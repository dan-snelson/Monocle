#!/bin/zsh --no-rcs
# Jamf Pro policy script (runs as root): saves the last day of installd log lines
# to /Library/Logs/ExampleOrg for later troubleshooting.

export PATH=/usr/bin:/bin:/usr/sbin:/sbin
umask 077

log_dir="/Library/Logs/ExampleOrg"

workdir=$(/usr/bin/mktemp -d /tmp/exampleorg.XXXXXX) || {
  echo "Error: mktemp failed"
  exit 1
}
trap '/bin/rm -rf -- "${workdir:?}"' EXIT

if ! /usr/bin/log show --last 1d --predicate 'process == "installd"' --style compact > "$workdir/installd.log"; then
  echo "Error: log show failed"
  exit 1
fi

/bin/mkdir -p -m 755 "$log_dir" || exit 1
if [[ -L "$log_dir" || ! -d "$log_dir" || "$(/usr/bin/stat -f %Su "$log_dir")" != "root" ]]; then
  echo "Error: $log_dir isn't a root-owned directory"
  exit 1
fi

destination="$log_dir/installd-$(/bin/date +%Y%m%d-%H%M%S).log"
/bin/mv -f "$workdir/installd.log" "$destination" || exit 1
echo "Saved $destination"
