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


printf "${RED}\n=====[DATATYPE PER I TIPI BUILT-IN]=====\n${NC}"
printf "\n${GREEN}(creazione e pubblicazione datatype built-in)\n${NC}"
create_and_publish "common" "string" "Stringa generica" "core.string"
create_and_publish "common" "integer" "Numero intero con segno" "core.integer"
create_and_publish "common" "number" "Numero reale" "core.number"
create_and_publish "common" "boolean" "Valore boolean" "core.boolean"
create_and_publish "common" "date" "Data in formato YYYY-MM-DD" "core.date"
create_and_publish "common" "datetime" "Data e ora in formato RFC3339, YYYY-MM-DDTHH:MM:SSZ o YYYY-MM-DDTHH:MM:SS+/-HH:MM" "core.datetime"
create_and_publish "network" "ip" "Singolo IP IPv4 o IPv6" "core.ip"
create_and_publish "network" "ip_prefix" "Prefisso valido in formato CIDR IPv4 o IPv6" "core.ip_prefix"

printf "\n${GREEN}(visualizzazione datatype creati tramite datatype list)\n${NC}"
"${CMD[@]}" datatype list

printf "\n${GREEN}(visualizzazione datatype creati tramite datatype list, json fmt)\n${NC}"
"${CMD[@]}" --output "json" datatype list




printf "${RED}\n=====[OPERAZIONI SU DATATYPE DERIVATO]=====\n${NC}"
printf "\n${GREEN}(creazione e pubblicazione datatype derivato common.email)\n${NC}"
create_and_publish "common" "email" "Indirizzo email" "core.string"

printf "\n${GREEN}(tentativo di creazione di un datatype duplicato; deve fallire)\n${NC}"
"${CMD[@]}" --output "json" datatype create --namespace "common" --name "email" --description "Indirizzo email" --base-type "core.string"

printf "\n${GREEN}(creazione nuova versione datatype derivato common.email)\n${NC}"
dtid=$("${CMD[@]}" --output "json" datatype show-name common email | jq -r '.id')
echo -e "recuperato id:${dtid}"
versnew=$("${CMD[@]}" --output "json" datatype version create ${dtid} --source-version 1 | jq -r '.version')
echo -e "creata nuova versione:${versnew}"

printf "\n${GREEN}(tentativo di creazione nuova versione da versione non pubblicata di common.email; deve fallire)\n${NC}"
dtid=$("${CMD[@]}" --output "json" datatype show-name common email | jq -r '.id')
echo -e "recuperato id:${dtid}"
"${CMD[@]}" --output "json" datatype version create ${dtid} --source-version ${versnew}

printf "\n${GREEN}(tentativo di modifica constraint pattern su versione pubblicata; deve fallire)\n${NC}"
"${CMD[@]}" --output "json" datatype version revise ${dtid} 1 --constraint 'pattern="^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"'

printf "\n${GREEN}(modifica constraint pattern su nuova versione non pubblicata)\n${NC}"
"${CMD[@]}" --output "json" datatype version revise ${dtid} ${versnew} --constraint 'pattern="^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"' 1>/dev/null 2>&1
echo -e "modificata versione:${versnew}"

printf "\n${GREEN}(stato attuale versioni)\n${NC}"
"${CMD[@]}" datatype version list ${dtid}

printf "\n${GREEN}(stato attuale versioni, json fmt)\n${NC}"
"${CMD[@]}" --output "json" datatype version list ${dtid}


printf "\n${GREEN}(aggiunta ulteriore constraint max_length su nuova versione non pubblicata)\n${NC}"
tmpfile=$(mktemp)
"${CMD[@]}" --output json datatype version show ${dtid} ${versnew} |
jq '
{
  constraints: (
    .constraints
    + [
        {
          "name": "max_length",
          "value": 254
        }
      ]
  )
}
' > "$tmpfile"

"${CMD[@]}" --output json datatype version revise ${dtid} ${versnew} --file "$tmpfile" 1>/dev/null 2>&1
rm "$tmpfile"
echo -e "modificata versione:${versnew}"


printf "\n${GREEN}(stato attuale versioni)\n${NC}"
"${CMD[@]}" datatype version list ${dtid}

printf "\n${GREEN}(stato attuale versioni, json fmt)\n${NC}"
"${CMD[@]}" --output "json" datatype version list ${dtid}

printf "\n${GREEN}(publish nuova versione e deprecate dell'altra)\n${NC}"
"${CMD[@]}" --output "json" datatype version publish ${dtid} ${versnew} 1>/dev/null 2>&1
"${CMD[@]}" --output "json" datatype version deprecate ${dtid} 1 1>/dev/null 2>&1
echo -e "versione deprecata:1"
echo -e "versione publish:${versnew}"

printf "\n${GREEN}(stato attuale versioni)\n${NC}"
"${CMD[@]}" datatype version list ${dtid}

printf "\n${GREEN}(stato attuale versioni, json fmt)\n${NC}"
"${CMD[@]}" --output "json" datatype version list ${dtid}

printf "\n${GREEN}(cancellazione datatype common.email)\n${NC}"
"${CMD[@]}" --output "json" datatype delete ${dtid}

printf "\n${GREEN}(lista datatype presenti)\n${NC}"
"${CMD[@]}" datatype list