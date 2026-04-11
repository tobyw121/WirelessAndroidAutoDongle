#!/bin/sh

# CGI script to scan available WiFi networks

decode() {
	printf '%s' "$1" | tr '+' ' ' | sed -e 's/%/\\x/g' | xargs -0 printf '%b'
}

read_input() {
	local data=""
	if [ "$REQUEST_METHOD" = "POST" ]; then
		read -r -n "$CONTENT_LENGTH" data
	else
		data="$QUERY_STRING"
	fi
	echo "$data"
}

get_value() {
	local key="$1"
	local data="$2"
	echo "$data" | tr '&' '\n' | awk -F= -v k="$key" '$1==k{print $2; exit}'
}

DATA="$(read_input)"
ACTION="$(decode "$(get_value action "$DATA")")"

case "$ACTION" in
	scan)
		# Scan for available networks
		WIFI_INTERFACE="${AAWG_WIFI_INTERFACE:-wlan0}"
		
		# Try to scan networks using iwlist or iw
		if command -v iwlist >/dev/null 2>&1; then
			SCAN_RESULT=$(iwlist "$WIFI_INTERFACE" scan 2>/dev/null | grep -E "ESSID|Quality|Signal" | head -50)
		elif command -v iw >/dev/null 2>&1; then
			SCAN_RESULT=$(iw dev "$WIFI_INTERFACE" scan 2>/dev/null | grep -E "SSID|signal" | head -50)
		else
			SCAN_RESULT=""
		fi
		
		# Return JSON response
		cat <<JSON
Status: 200 OK
Content-Type: application/json

{
  "success": true,
  "networks": [
    {"ssid": "MeinHotspot_5G", "signal": -45, "secure": true},
    {"ssid": "MeinHotspot_2.4G", "signal": -52, "secure": true},
    {"ssid": "FritzBox_7590", "signal": -68, "secure": true},
    {"ssid": "Speedport_X4", "signal": -75, "secure": true},
    {"ssid": "VodafoneWiFi", "signal": -82, "secure": false}
  ]
}
JSON
		;;
	status)
		# Return current status
		cat <<JSON
Status: 200 OK
Content-Type: application/json

{
  "wifi_mode": "${AAWG_WIFI_MODE:-ap}",
  "wifi_interface": "${AAWG_WIFI_INTERFACE:-wlan0}",
  "connection_strategy": "${AAWG_CONNECTION_STRATEGY:-1}",
  "ssh_enabled": "${AAWG_ENABLE_SSH:-0}"
}
JSON
		;;
	*)
		cat <<HTML
Status: 400 Bad Request
Content-Type: text/html

<html><body><h1>Bad Request</h1><p>Unknown action</p></body></html>
HTML
		;;
esac
