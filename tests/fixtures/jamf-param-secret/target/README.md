# Set Asset Tag

Records each Mac's serial number in its Jamf Pro **Asset Tag** field.

- **Deploy:** a Jamf Pro policy (runs as root) scoped to All Computers, once per computer.
- **API client:** create an API role with the **Update Computers** privilege and an API client that uses it.
- **Parameters:** 4, Jamf Pro URL; 5, API client ID; 6, API client secret; 7, the computer's Jamf Pro ID.
