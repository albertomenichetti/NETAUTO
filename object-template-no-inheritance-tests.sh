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







printf "${RED}\n[INTERAZIONE DATATYPE E OBJECTTEMPLATE NO INHERITANCE]\n${NC}"

printf "\n${GREEN}(creazione datatype derivato common.email)\n${NC}"
"${CMD[@]}" --output "json" datatype create --namespace "common" --name "email" --description "Indirizzo email" --base-type "core.string" 1>/dev/null 2>&1
dtid=$("${CMD[@]}" --output "json" datatype show-name common email | jq -r '.id')
echo -e "id:${dtid}"

printf "\n${GREEN}(versioni e stato datatype common.email)\n${NC}"
"${CMD[@]}" datatype version list ${dtid}

printf "\n${GREEN}(tentativo di creazione objecttemplate test_template che usa common.email, deve fallire perchè common.email non è pubblicato)\n${NC}"
"${CMD[@]}" --output json object-template create --namespace test --name test_template --description "Template di test" --property-json "{\"name\": \"e_mail\", \"datatype_id\": \"$dtid\", \"required\": false}"

printf "\n${GREEN}(pubblicazione datatype derivato common.email)\n${NC}"
echo -e "recuperato id:${dtid}"
"${CMD[@]}" --output "json" datatype version publish ${dtid} 1 1>/dev/null 2>&1

printf "\n${GREEN}(versioni e stato datatype common.email)\n${NC}"
"${CMD[@]}" datatype version list ${dtid}

printf "\n${GREEN}(creazione objecttemplate test_template che usa common.email)\n${NC}"
otid=$("${CMD[@]}" --output json object-template create --namespace test --name test_template --description "Template di test" --property-json "{\"name\": \"e_mail\", \"datatype_id\": \"$dtid\", \"required\": false}" | jq -r '.object_template.id')
echo -e "id:${otid}"

printf "\n${GREEN}(lista objecttemplate presenti)\n${NC}"
"${CMD[@]}" object-template list

printf "\n${GREEN}(lista objecttemplate presenti, json fmt)\n${NC}"
"${CMD[@]}" --output "json" object-template list

printf "\n${GREEN}(versioni objecttemplate test_template presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}

printf "\n${GREEN}(tentativo di cancellazione datatype common.email, deve fallire perchè è in uso a test_template)\n${NC}"
"${CMD[@]}" --output "json" datatype delete ${dtid}

printf "\n${GREEN}(deprecate dell'unica versione common.email)\n${NC}"
"${CMD[@]}" --output "json" datatype version deprecate ${dtid} 1 1>/dev/null 2>&1
echo -e "done"

printf "\n${GREEN}(versioni e stato datatype common.email)\n${NC}"
"${CMD[@]}" datatype version list ${dtid}

printf "\n${GREEN}(tentativo di creazione objecttemplate test_template2 che usa common.email, deve fallire perchè common.email ha un'unica versione ed è deprecata)\n${NC}"
"${CMD[@]}" --output json object-template create --namespace test --name test_template2 --description "Template di test2" --property-json "{\"name\": \"e_mail\", \"datatype_id\": \"$dtid\", \"required\": false}"

printf "\n${GREEN}(creazione di due nuove versioni di datatype derivato common.email)\n${NC}"
versnew1=$("${CMD[@]}" --output "json" datatype version create ${dtid} --source-version 1 | jq -r '.version')
echo -e "creata nuova versione:${versnew1}"
versnew2=$("${CMD[@]}" --output "json" datatype version create ${dtid} --source-version 1 | jq -r '.version')
echo -e "creata nuova versione:${versnew2}"
"${CMD[@]}" --output "json" datatype version publish ${dtid} ${versnew1} 1>/dev/null 2>&1
echo -e "pubblicata nuova versione:${versnew1}"
"${CMD[@]}" --output "json" datatype version publish ${dtid} ${versnew2} 1>/dev/null 2>&1
echo -e "pubblicata nuova versione:${versnew2}"

printf "\n${GREEN}(versioni e stato datatype common.email)\n${NC}"
"${CMD[@]}" datatype version list ${dtid}

printf "\n${GREEN}(creazione objecttemplate test_template2 che usa common.email; senza version pinning specifico userà la versione più grande)\n${NC}"
otid=$("${CMD[@]}" --output json object-template create --namespace test --name test_template2 --description "Template di test" --property-json "{\"name\": \"e_mail\", \"datatype_id\": \"$dtid\", \"required\": false}" | jq -r '.object_template.id')
echo -e "id:${otid}"

printf "\n${GREEN}(versioni objecttemplate test_template2 presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}

printf "\n${GREEN}(creazione objecttemplate test_template3 che usa common.email; pinning specifico su versione 2)\n${NC}"
otid=$("${CMD[@]}" --output json object-template create --namespace test --name test_template3 --description "Template di test" --property-json "{\"name\": \"e_mail\", \"datatype_id\": \"$dtid\", \"datatype_version\": 2, \"required\": false}" | jq -r '.object_template.id')
echo -e "id:${otid}"

printf "\n${GREEN}(versioni objecttemplate test_template3 presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}

printf "\n${GREEN}(tentativo di creazione di una nuova versione dell'objecttemplate test_template2; deve fallire perchè lo stato non è published)\n${NC}"
otid=$("${CMD[@]}" --output json object-template show-name test test_template2 | jq -r '.id')
echo -e "id:${otid}"
"${CMD[@]}" --output json object-template version create ${otid} --source-version 1

printf "\n${GREEN}(publish della versione 1 di test_template2)\n${NC}"
"${CMD[@]}" --output json object-template version publish ${otid} 1 1>/dev/null 2>&1
echo -e "pubblicata versione:1"

printf "\n${GREEN}(versioni objecttemplate test_template2 presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}

printf "\n${GREEN}(creazione di una nuova versione dell'objecttemplate test_template2)\n${NC}"
otid=$("${CMD[@]}" --output json object-template show-name test test_template2 | jq -r '.id')
echo -e "id:${otid}"
"${CMD[@]}" --output json object-template version create ${otid} --source-version 1 1>/dev/null 2>&1

printf "\n${GREEN}(versioni objecttemplate test_template2 presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}


printf "\n${GREEN}(modifica su objecttemplate test_template2 v2 del valore required a true sul campo e_mail)\n${NC}"
tmpfile=$(mktemp)
"${CMD[@]}" --output json object-template version show ${otid} 2 |
jq '
{ parent: .parent,
  properties: (
    .properties
    | map(
        if .name == "e_mail"
        then .required = true
        else .
        end
      )
  ),
  components: .components
}
' > "$tmpfile"

"${CMD[@]}" --output json object-template version revise ${otid} 2 --file "$tmpfile" 1>/dev/null 2>&1
rm "$tmpfile"
echo -e "done"


printf "\n${GREEN}(versioni objecttemplate test_template2 presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}


printf "\n${GREEN}(tentativo di modifica su objecttemplate test_template2 v2 del valore del datatype_version da 3 a 2 sul campo e_mail; deve fallire downgrade non ammesso)\n${NC}"
tmpfile=$(mktemp)
"${CMD[@]}" --output json object-template version show ${otid} 2 |
jq '
{ parent: .parent,
  properties: (
    .properties
    | map(
        if .name == "e_mail"
        then .datatype_version = 2
        else .
        end
      )
  ),
  components: .components
}
' > "$tmpfile"

"${CMD[@]}" --output json object-template version revise ${otid} 2 --file "$tmpfile"
rm "$tmpfile"


printf "\n${GREEN}(versioni objecttemplate test_template2 presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}


printf "\n${GREEN}(publish della versione 1 di test_template3)\n${NC}"
otid=$("${CMD[@]}" --output json object-template show-name test test_template3 |
jq -r '.id')
"${CMD[@]}" --output json object-template version publish ${otid} 1 1>/dev/null 2>&1
echo -e "pubblicata versione:1"

printf "\n${GREEN}(creazione di una nuova versione dell'objecttemplate test_template3)\n${NC}"
otid=$("${CMD[@]}" --output json object-template show-name test test_template3 | jq -r '.id')
echo -e "id:${otid}"
"${CMD[@]}" --output json object-template version create ${otid} --source-version 1 1>/dev/null 2>&1

printf "\n${GREEN}(versioni objecttemplate test_template3 presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}


printf "\n${GREEN}(modifica su objecttemplate test_template3 v2 del valore del datatype_version da 2 a 3 sul campo e_mail; è un upgrade quindi deve essere ammesso)\n${NC}"
tmpfile=$(mktemp)
"${CMD[@]}" --output json object-template version show ${otid} 2 |
jq '
{ parent: .parent,
  properties: (
    .properties
    | map(
        if .name == "e_mail"
        then .datatype_version = 3
        else .
        end
      )
  ),
  components: .components
}
' > "$tmpfile"

"${CMD[@]}" --output json object-template version revise ${otid} 2 --file "$tmpfile"
rm "$tmpfile"


printf "\n${GREEN}(versioni objecttemplate test_template3 presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}

printf "\n${GREEN}(creazione datatype derivato common.serial_number)\n${NC}"
"${CMD[@]}" --output "json" datatype create --namespace "common" --name "serial_number" --description "Numero di serie" --base-type "core.string" 1>/dev/null 2>&1
dtid=$("${CMD[@]}" --output "json" datatype show-name common serial_number | jq -r '.id')
echo -e "id:${dtid}"

printf "\n${GREEN}(pubblicazione datatype derivato common.serial_number)\n${NC}"
echo -e "recuperato id:${dtid}"
"${CMD[@]}" --output "json" datatype version publish ${dtid} 1 1>/dev/null 2>&1

printf "\n${GREEN}(versioni e stato datatype common.serial_number)\n${NC}"
"${CMD[@]}" datatype version list ${dtid}

printf "\n${GREEN}(creazione objecttemplate test_newtemplate di tipo abstract che usa common.email e common.serial_number, quest'ultimo è required)\n${NC}"
dtid1=$("${CMD[@]}" --output "json" datatype show-name common email | jq -r '.id')
dtid2=$("${CMD[@]}" --output "json" datatype show-name common serial_number | jq -r '.id')
otid=$("${CMD[@]}" --output json object-template create --namespace test --name test_newtemplate --description "Nuovo Template di test" --abstract \
--property-json "{\"name\": \"e_mail\", \"datatype_id\": \"$dtid1\", \"required\": false}" \
--property-json "{\"name\": \"serial_number\", \"datatype_id\": \"$dtid2\", \"required\": true}"| jq -r '.object_template.id')
echo -e "id:${otid}"

printf "\n${GREEN}(versioni objecttemplate test_newtemplate presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}

printf "\n${GREEN}(publish della versione 1 di test_newtemplate)\n${NC}"
"${CMD[@]}" --output json object-template version publish ${otid} 1 1>/dev/null 2>&1
echo -e "pubblicata versione:1"

printf "\n${GREEN}(creazione di una nuova versione dell'objecttemplate test_newtemplate)\n${NC}"
echo -e "id:${otid}"
"${CMD[@]}" --output json object-template version create ${otid} --source-version 1 1>/dev/null 2>&1

printf "\n${GREEN}(versioni objecttemplate test_newtemplate presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}


printf "\n${GREEN}(rimozione della proprietà serial_number dalla versione 2 di test_newtemplate)\n${NC}"
tmpfile=$(mktemp)
"${CMD[@]}" --output json object-template version show ${otid} 2 |
jq '
{
  parent: .parent,
  properties: [
    .properties[]
    | select(.name != "serial_number")
  ],
  components: .components
}
' > "$tmpfile"

"${CMD[@]}" --output json object-template version revise ${otid} 2 --file "$tmpfile" 1>/dev/null 2>&1
rm "$tmpfile"
echo -e "done"


printf "\n${GREEN}(versioni objecttemplate test_newtemplate presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}

printf "\n${GREEN}(creazione objecttemplate network_interface con properties if_name e if_speed)\n${NC}"
dtid1=$("${CMD[@]}" --output "json" datatype show-name common string | jq -r '.id')
dtid2=$("${CMD[@]}" --output "json" datatype show-name common integer | jq -r '.id')
otid=$("${CMD[@]}" --output json object-template create --namespace network --name network_interface --description "Interfaccia di rete" \
--property-json "{\"name\": \"if_name\", \"datatype_id\": \"$dtid1\", \"required\": true}" \
--property-json "{\"name\": \"if_speed\", \"datatype_id\": \"$dtid2\", \"required\": false}"| jq -r '.object_template.id')
echo -e "id:${otid}"

printf "\n${GREEN}(publish della versione 1 di network_interface)\n${NC}"
"${CMD[@]}" --output json object-template version publish ${otid} 1 1>/dev/null 2>&1
echo -e "pubblicata versione:1"

printf "\n${GREEN}(versioni objecttemplate network_interface presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid}

printf "\n${GREEN}(creazione objecttemplate supervisor con properties serial_number)\n${NC}"
dtid3=$("${CMD[@]}" --output "json" datatype show-name common serial_number | jq -r '.id')
otid2=$("${CMD[@]}" --output json object-template create --namespace network --name supervisor --description "Router supervisor" \
--property-json "{\"name\": \"serial_number\", \"datatype_id\": \"$dtid3\", \"required\": true}"| jq -r '.object_template.id')
echo -e "id:${otid2}"

printf "\n${GREEN}(publish della versione 1 di supervisor)\n${NC}"
"${CMD[@]}" --output json object-template version publish ${otid2} 1 1>/dev/null 2>&1
echo -e "pubblicata versione:1"

printf "\n${GREEN}(versioni objecttemplate supervisor presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid2}

printf "\n${GREEN}(creazione objecttemplate router con properties host_name e components network_interface e supervisor)\n${NC}"
otid3=$("${CMD[@]}" --output json object-template create --namespace network --name router --description "Router Device" \
--property-json "{\"name\": \"host_name\", \"datatype_id\": \"$dtid1\", \"required\": true}" \
--component-json "{\"name\": \"interfaces\", \"template_id\": \"$otid\"}" \
--component-json "{\"name\": \"supervisors\", \"template_id\": \"$otid2\"}"| jq -r '.object_template.id')
echo -e "id:${otid3}"

printf "\n${GREEN}(publish della versione 1 di router)\n${NC}"
"${CMD[@]}" --output json object-template version publish ${otid3} 1 1>/dev/null 2>&1
echo -e "pubblicata versione:1"

printf "\n${GREEN}(versioni objecttemplate router presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid3}

printf "\n${GREEN}(creazione di una nuova versione dell'objecttemplate router)\n${NC}"
echo -e "id:${otid3}"
"${CMD[@]}" --output json object-template version create ${otid3} --source-version 1 1>/dev/null 2>&1

printf "\n${GREEN}(rimozione del component supervisors dalla versione 2 di router)\n${NC}"
tmpfile=$(mktemp)
"${CMD[@]}" --output json object-template version show ${otid3} 2 |
jq '
{
  parent: .parent,
  properties: .properties,
  components: [
    .components[]
    | select(.name != "supervisors")
  ]
}
' > "$tmpfile"

"${CMD[@]}" --output json object-template version revise ${otid3} 2 --file "$tmpfile" 1>/dev/null 2>&1
rm "$tmpfile"
echo -e "done"


printf "\n${GREEN}(versioni objecttemplate router presenti, json fmt)\n${NC}"
"${CMD[@]}" --output json object-template version list ${otid3}

