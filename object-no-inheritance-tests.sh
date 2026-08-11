#!/usr/bin/env bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

CMD=(.local/bin/uv run netauto)

if ! command -v jq >/dev/null 2>&1; then
    echo "Errore: jq non è installato o non è disponibile nel PATH." >&2
    exit 1
fi

create_and_publish() {
    local namespace="$1"
    local name="$2"
    local description="$3"
    local base_type="$4"

    echo -n "Creazione ${namespace}.${name} (${base_type})"

    local result
    result=$(
        "${CMD[@]}" --output "json" datatype create \
            --namespace "$namespace" \
            --name "$name" \
            --description "$description" \
            --base-type "$base_type"
    )

    local datatype_id
    datatype_id=$(printf '%s' "$result" | jq -r '.datatype.id')

    if [[ -z "$datatype_id" || "$datatype_id" == "null" ]]; then
        echo "Errore: impossibile recuperare l'ID di ${namespace}.${name}" >&2
        echo "$result" >&2
        exit 1
    fi

    echo -n " id:$datatype_id"

    "${CMD[@]}" --output "json" datatype version publish "$datatype_id" 1 1>/dev/null 2>&1

    echo -n " publish:v1"
    echo
}


create_and_publish "common" "string" "Stringa generica" "core.string" 1>/dev/null 2>&1
create_and_publish "common" "integer" "Numero intero con segno" "core.integer" 1>/dev/null 2>&1
create_and_publish "common" "number" "Numero reale" "core.number" 1>/dev/null 2>&1
create_and_publish "common" "boolean" "Valore boolean" "core.boolean" 1>/dev/null 2>&1
create_and_publish "common" "date" "Data in formato YYYY-MM-DD" "core.date" 1>/dev/null 2>&1
create_and_publish "common" "datetime" "Data e ora in formato RFC3339, YYYY-MM-DDTHH:MM:SSZ o YYYY-MM-DDTHH:MM:SS+/-HH:MM" "core.datetime" 1>/dev/null 2>&1
create_and_publish "network" "ip" "Singolo IP IPv4 o IPv6" "core.ip" 1>/dev/null 2>&1
create_and_publish "network" "ip_prefix" "Prefisso valido in formato CIDR IPv4 o IPv6" "core.ip_prefix" 1>/dev/null 2>&1

dtidstring=$("${CMD[@]}" --output "json" datatype show-name common string | jq -r '.id')
dtidinteger=$("${CMD[@]}" --output "json" datatype show-name common integer | jq -r '.id')

otidnetif=$("${CMD[@]}" --output json object-template create --namespace network --name network_interface --description "Interfaccia di rete" \
--property-json "{\"name\": \"if_name\", \"datatype_id\": \"$dtidstring\", \"required\": true}" \
--property-json "{\"name\": \"if_speed\", \"datatype_id\": \"$dtidinteger\", \"required\": false}"| jq -r '.object_template.id')

otidsuperv=$("${CMD[@]}" --output json object-template create --namespace network --name supervisor --description "Network Supervisor" \
--property-json "{\"name\": \"serial_number\", \"datatype_id\": \"$dtidstring\", \"required\": true}" \
--property-json "{\"name\": \"cpu\", \"datatype_id\": \"$dtidstring\", \"required\": true}" \
--property-json "{\"name\": \"ram_gb\", \"datatype_id\": \"$dtidinteger\", \"required\": false}" | jq -r '.object_template.id')

"${CMD[@]}" --output json object-template version publish ${otidnetif} 1 1>/dev/null 2>&1
#"${CMD[@]}" --output json object-template version publish ${otidsuperv} 1 1>/dev/null 2>&1