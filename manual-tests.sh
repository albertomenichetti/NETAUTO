#!/usr/bin/env bash

set -euo pipefail

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

printf "${RED}\n[CREAZIONE E PUBBLICAZIONE DATATYPE PER I TIPI BUILT-IN]\n${NC}"
create_and_publish "common" "string" "Stringa generica" "core.string"
create_and_publish "common" "integer" "Numero intero con segno" "core.integer"
create_and_publish "common" "number" "Numero reale" "core.number"
create_and_publish "common" "boolean" "Valore boolean" "core.boolean"
create_and_publish "common" "date" "Data in formato YYYY-MM-DD" "core.date"
create_and_publish "common" "datetime" "Data e ora in formato RFC3339, YYYY-MM-DDTHH:MM:SSZ o YYYY-MM-DDTHH:MM:SS+/-HH:MM" "core.datetime"
create_and_publish "network" "ip" "Singolo IP IPv4 o IPv6" "core.ip"
create_and_publish "network" "ip_prefix" "Prefisso valido in formato CIDR IPv4 o IPv6" "core.ip_prefix"



printf "${RED}\n[ USO FUNZIONE DATATYPE LIST ]\n${NC}"
"${CMD[@]}" datatype list



printf "${RED}\n[CREAZIONE E PUBBLICAZIONE DATATYPE DERIVATO]\n${NC}"
create_and_publish "common" "email" "Stringa generica" "core.string"



printf "${RED}\n[CREAZIONE E MODIFICA NUOVA VERSIONE DATATYPE DERIVATO]\n${NC}"
dtid=$("${CMD[@]}" --output "json" datatype show-name common datetime | jq -r '.id')
echo -e "recuperato id:${dtid}"
versnew=$("${CMD[@]}" --output "json" datatype version create ${dtid} --source-version 1 | jq -r '.version')
echo -e "creata nuova versione:${versnew}"
"${CMD[@]}" --output "json" datatype version revise ${dtid} ${versnew} --base-type core.string --constraint 'pattern="^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"' 1>/dev/null 2>&1
echo -e "modificata versione:${versnew}"



printf "${RED}\n[STATO ATTUALE VERSIONI]\n${NC}"
"${CMD[@]}" datatype version list ${dtid}



printf "${RED}\n[STATO ATTUALE VERSIONI (json)]\n${NC}"
"${CMD[@]}" --output "json" datatype version list ${dtid}



printf "${RED}\n[PUBLISH NUOVA VERSIONE E DEPRECATE DELL'ALTRA]\n${NC}"
"${CMD[@]}" --output "json" datatype version publish ${dtid} ${versnew} 1>/dev/null 2>&1
"${CMD[@]}" --output "json" datatype version deprecate ${dtid} 1 1>/dev/null 2>&1
echo -e "versione deprecata:1"
echo -e "versione publish:${versnew}"



printf "${RED}\n[STATO ATTUALE VERSIONI]\n${NC}"
"${CMD[@]}" datatype version list ${dtid}



printf "${RED}\n[STATO ATTUALE VERSIONI (json)]\n${NC}"
"${CMD[@]}" --output "json" datatype version list ${dtid}