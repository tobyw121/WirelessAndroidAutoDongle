#!/bin/sh

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

WIFI_MODE="$(decode "$(get_value wifi_mode "$DATA")")"
WIFI_CLIENT_SSID="$(decode "$(get_value wifi_client_ssid "$DATA")")"
WIFI_CLIENT_PASSWORD="$(decode "$(get_value wifi_client_password "$DATA")")"
WIFI_PASSWORD="$(decode "$(get_value wifi_password "$DATA")")"
WIFI_INTERFACE="$(decode "$(get_value wifi_interface "$DATA")")"
COUNTRY_CODE="$(decode "$(get_value country_code "$DATA")")"
CONNECTION_STRATEGY="$(decode "$(get_value connection_strategy "$DATA")")"
ENABLE_SSH="$(decode "$(get_value enable_ssh "$DATA")")"

cat > /etc/aawgd.conf <<EOF
#!/bin/sh

######## Configuration options for Android Auto Wireless Dongle ########

AAWG_COUNTRY_CODE=${COUNTRY_CODE:-IN}
AAWG_CONNECTION_STRATEGY=${CONNECTION_STRATEGY:-1}
AAWG_UNIQUE_NAME_SUFFIX=

######## Advanced Configuration ########

AAWG_WIFI_PASSWORD=${WIFI_PASSWORD:-AAAtest!!}
AAWG_WIFI_MODE=${WIFI_MODE:-ap}
AAWG_WIFI_INTERFACE=${WIFI_INTERFACE:-wlan0}
AAWG_WIFI_CLIENT_SSID=${WIFI_CLIENT_SSID}
AAWG_WIFI_CLIENT_PASSWORD=${WIFI_CLIENT_PASSWORD}
AAWG_ENABLE_WEB_UI=1
AAWG_ENABLE_SSH=${ENABLE_SSH:-0}
EOF

cat <<'HTML'
Status: 200 OK
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html lang="de">
  <head>
    <meta charset="utf-8" />
    <title>Konfiguration gespeichert</title>
    <style>
      body { font-family: system-ui, sans-serif; background: #0b1220; color: #f8fafc; padding: 24px; }
      .card { max-width: 560px; margin: 0 auto; background: #111827; padding: 24px; border-radius: 12px; }
      a { color: #38bdf8; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>Gespeichert ✅</h1>
      <p>Die Konfiguration wurde gespeichert. Bitte starte den Dongle neu, damit die Änderungen aktiv werden.</p>
      <p><a href="/">Zurück</a></p>
    </div>
  </body>
</html>
HTML
