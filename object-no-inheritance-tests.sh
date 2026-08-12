#!/usr/bin/env bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

CMD_JSON=(.local/bin/uv run netauto --output json)
CMD=(.local/bin/uv run netauto)



read -r dtstring version < <(
  "${CMD_JSON[@]}" datatype create --namespace common --name string --description "Stringa generica" --base-type core.string | jq -r '[.datatype.id, .version.version] | @tsv'
)
"${CMD_JSON[@]}" datatype version publish "$dtstring" "$version" 1>/dev/null

read -r dtint version < <(
  "${CMD_JSON[@]}" datatype create --namespace common --name integer --description "Numero intero con segno" --base-type core.integer | jq -r '[.datatype.id, .version.version] | @tsv'
)
"${CMD_JSON[@]}" datatype version publish "$dtint" "$version" 1>/dev/null

read -r dtnumber version < <(
  "${CMD_JSON[@]}" datatype create --namespace common --name number --description "Numero reale" --base-type core.number | jq -r '[.datatype.id, .version.version] | @tsv'
)
"${CMD_JSON[@]}" datatype version publish "$dtnumber" "$version" 1>/dev/null

read -r dtboolean version < <(
  "${CMD_JSON[@]}" datatype create --namespace common --name boolean --description "Valore boolean" --base-type core.boolean | jq -r '[.datatype.id, .version.version] | @tsv'
)
"${CMD_JSON[@]}" datatype version publish "$dtboolean" "$version" 1>/dev/null

read -r dtdate version < <(
  "${CMD_JSON[@]}" datatype create --namespace common --name date --description "Data in formato YYYY-MM-DD" --base-type core.date | jq -r '[.datatype.id, .version.version] | @tsv'
)
"${CMD_JSON[@]}" datatype version publish "$dtdate" "$version" 1>/dev/null

read -r dtdatetime version < <(
  "${CMD_JSON[@]}" datatype create --namespace common --name datetime --description "Data e ora in formato RFC3339, YYYY-MM-DDTHH:MM:SSZ o YYYY-MM-DDTHH:MM:SS+/-HH:MM" --base-type core.datetime | jq -r '[.datatype.id, .version.version] | @tsv'
)
"${CMD_JSON[@]}" datatype version publish "$dtdatetime" "$version" 1>/dev/null

read -r dtip version < <(
  "${CMD_JSON[@]}" datatype create --namespace common --name ip --description "Singolo IP IPv4 o IPv6" --base-type core.ip | jq -r '[.datatype.id, .version.version] | @tsv'
)
"${CMD_JSON[@]}" datatype version publish "$dtip" "$version" 1>/dev/null

read -r dtipprefix version < <(
  "${CMD_JSON[@]}" datatype create --namespace common --name ip_prefix --description "Prefisso valido in formato CIDR IPv4 o IPv6" --base-type core.ip_prefix | jq -r '[.datatype.id, .version.version] | @tsv'
)
"${CMD_JSON[@]}" datatype version publish "$dtipprefix" "$version" 1>/dev/null






#####
printf "\n${GREEN}(lista datatype built-in presenti)\n${NC}"
"${CMD[@]}" datatype list

#####
printf "\n${GREEN}(creazione e pubblicazione objecttemplate network_interface)\n${NC}"
read -r otidnetif otvernetif < <(
  "${CMD_JSON[@]}" object-template create --namespace network --name network_interface --description "Interfaccia di rete" \
  --property-json "{\"name\": \"if_name\", \"datatype_id\": \"$dtstring\", \"required\": true}" \
  --property-json "{\"name\": \"if_speed\", \"datatype_id\": \"$dtint\", \"required\": false}"  | jq -r '[.object_template.id, .version.version] | @tsv'
)
"${CMD_JSON[@]}" object-template version publish "$otidnetif" "$otvernetif" 1>/dev/null
echo -e "id:$otidnetif, version:$otvernetif"

#####
printf "\n${GREEN}(creazione senza pubblicazione objecttemplate supervisor)\n${NC}"
read -r otidsuperv otversuperv < <(
  "${CMD_JSON[@]}" object-template create --namespace network --name supervisor --description "Network Supervisor" \
  --property-json "{\"name\": \"serial_number\", \"datatype_id\": \"$dtstring\", \"required\": true}" \
  --property-json "{\"name\": \"cpu\", \"datatype_id\": \"$dtstring\", \"required\": true}" \
  --property-json "{\"name\": \"ram_gb\", \"datatype_id\": \"$dtint\", \"required\": false}"  | jq -r '[.object_template.id, .version.version] | @tsv'
)
echo -e "id:$otidsuperv, version:$otversuperv"

#####
printf "\n${GREEN}(creazione oggetto di tipo network_interface senza version pinning e senza property if_speed dato che al momento è optional)\n${NC}"
read -r obnetif1 < <(
  "${CMD_JSON[@]}" object create --template-id $otidnetif --property-json '{"if_name":"Ethernet-0/1"}'  | jq -r '[.id] | @tsv'
)
"${CMD[@]}" object show "$obnetif1"

#####
printf "\n${GREEN}(creazione oggetto di tipo network_interface senza version pinning ma anche con la property if_speed)\n${NC}"
read -r obnetif2 < <(
  "${CMD_JSON[@]}" object create --template-id $otidnetif --property-json '{"if_name":"Ethernet-0/2","if_speed":1000}'  | jq -r '[.id] | @tsv'
)
"${CMD[@]}" object show "$obnetif2"

#####
printf "\n${GREEN}(test creazione oggetto di tipo supervisor; deve fallire, non ha versioni published)\n${NC}"
"${CMD_JSON[@]}" object create --template-id $otidsuperv --property-json '{"serial_number":"SN12345","cpu":"Intel Xeon","ram_gb":16}'

#####
printf "\n${GREEN}(creazione e publish di una nuova versione di objecttemplate network_interface)\n${NC}"
read -r otvernetif2 < <(
  "${CMD_JSON[@]}" object-template version create  $otidnetif --source-version $otvernetif  | jq -r '[.version] | @tsv'
)
"${CMD_JSON[@]}" object-template version publish "$otidnetif" "$otvernetif2" 1>/dev/null
echo -e "id:$otidnetif, version:$otvernetif2"

#####
printf "\n${GREEN}(creazione e publish di una ulteriore versione di objecttemplate network_interface, che rende if_speed obbligatorio)\n${NC}"
read -r otvernetif3 < <(
  "${CMD_JSON[@]}" object-template version create  $otidnetif --source-version $otvernetif  | jq -r '[.version] | @tsv'
)

"${CMD_JSON[@]}" object-template version revise "$otidnetif" "$otvernetif3" \
  --property-json "{\"name\": \"if_name\", \"datatype_id\": \"$dtstring\", \"required\": true}" \
  --property-json "{\"name\": \"if_speed\", \"datatype_id\": \"$dtint\", \"required\": true}" 1>/dev/null

#"${CMD_JSON[@]}" object-template version publish "$otidnetif" "$otvernetif3" 1>/dev/null
#echo -e "id:$otidnetif, version:$otvernetif2"

#####
printf "\n${GREEN}(verifica stato versioni objecttemplate network_interface)\n${NC}"
"${CMD_JSON[@]}" object-template version list "$otidnetif"