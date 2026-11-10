#!/bin/zsh --no-rcs
# Jamf Pro policy script (runs as root): records this Mac's serial number in its
# Jamf Pro Asset Tag field through the Jamf Pro API.
#
# Parameter 4: Jamf Pro URL, for example https://example.jamfcloud.invalid
# Parameter 5: API client ID
# Parameter 6: API client secret (API role privilege: Update Computers)
# Parameter 7: this Mac's Jamf Pro computer ID

export PATH=/usr/bin:/bin:/usr/sbin:/sbin

jamf_url="${4%/}"
client_id="$5"
client_secret="$6"
computer_id="$7"

if [[ -z "$jamf_url" || -z "$client_id" || -z "$client_secret" || "$computer_id" != <-> ]]; then
  echo "Error: Parameters 4 through 7 are required"
  exit 1
fi

serial=$(/usr/sbin/ioreg -rd1 -c IOPlatformExpertDevice | /usr/bin/awk -F'"' '/IOPlatformSerialNumber/ { print $4 }')
if [[ ! "$serial" =~ '^[A-Z0-9]+$' ]]; then
  echo "Error: could not read the serial number"
  exit 1
fi

response=$(printf 'grant_type=client_credentials&client_id=%s&client_secret=%s' "$client_id" "$client_secret" |
  /usr/bin/curl --silent --fail --proto '=https' --max-time 30 --data @- "$jamf_url/api/oauth/token") || {
  echo "Error: token request failed"
  exit 1
}

token=$(print -r -- "$response" | /usr/bin/plutil -extract access_token raw -o - -) || {
  echo "Error: no access token in the response"
  exit 1
}

printf '{"general":{"assetTag":"%s"}}' "$serial" |
  /usr/bin/curl --silent --fail --proto '=https' --max-time 30 --request PATCH \
    --header "Content-Type: application/json" --oauth2-bearer "$token" \
    --data @- "$jamf_url/api/v1/computers-inventory-detail/$computer_id" > /dev/null || {
  echo "Error: the Asset Tag update failed"
  exit 1
}

echo "Asset Tag set to $serial"
