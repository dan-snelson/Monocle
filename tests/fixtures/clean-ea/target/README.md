# Battery Cycle Count

A Jamf Pro Extension Attribute that reports a Mac's battery cycle count.

- **Deploy:** add `battery-cycle-count.zsh` as a Jamf Pro Extension Attribute (Data Type: String). Jamf Pro runs it as root during inventory.
- **Results:** the cycle count, `No battery` on desktops, or a line starting with `Error:`.
- **Side effects:** none. It only reads I/O Registry data.
