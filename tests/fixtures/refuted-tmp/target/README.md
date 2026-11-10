# Save installd Log

Saves the last day of `installd` unified-log lines to `/Library/Logs/ExampleOrg/` so support staff can review failed installs.

- **Deploy:** a Jamf Pro policy (runs as root), on demand.
- **Output:** one root-only log file per run, named with the date and time.
