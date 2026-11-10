# Remove Apps

Removes Zoom, Slack, or Microsoft Teams so users can clean up apps they no longer need.

- **Deploy:** a Jamf Pro Self Service policy (runs as root). Create one policy per set of apps you offer.
- **Parameter 4:** comma-separated app names from this list: `Zoom`, `Slack`, `Teams`. Leave it blank and the policy removes nothing. An unknown name fails the policy.
- **What it removes:** only the app bundle in `/Applications`. User data and preferences stay.
