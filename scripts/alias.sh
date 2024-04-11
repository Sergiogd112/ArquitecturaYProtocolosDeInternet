alias lxat='lxc-attach'
alias sbashrc="source ~/.bashrc"
alias tpth_api="tracepath_api"
alias cpract="cd /home/api/practiques"
function lxvt(){
    lxc-attach -n $1 -- vtysh
}
function lxvtrc(){
    lxc-attach -n $1 -- vtysh -c "show running-config"
}

function lxvtc(){
    lxc-attach -n $1 -- vtysh -c "$2"
}
function lxcc(){
    lxc-attach -n $1 -- $2
}

function pimd_conf_search() {
  # Define colors using tput
  yellow=$(tput setaf 3)
  red=$(tput setaf 1)
  green=$(tput setaf 2)
  blue=$(tput setaf 4)
  reset=$(tput sgr0)
  echo -e "=================================================" # Add an equal sign separator
  echo -e "=================================================\n" # Add an equal sign separator
  # Find files that start with "pimd.conf" in the current directory and its subdirectories,
  # sort them alphabetically, and then process each file
  find . -type f -name 'pimd.conf*' | sort | while read -r file; do
    # Extract the part of the file path after "pimd.conf"
    highlighted_path=$(echo "$file" | sed -E 's/.*pimd\.conf//')
    # Echo the file path with highlighted text in yellow
echo ""
    echo -e "${yellow}File: pimd.conf${blue}${highlighted_path}${reset}"
    # Use grep to search for and highlight the desired patterns in the file content
    cat "$file" | awk '{for (i=1; i<=NF; i++) { if ($i ~ /cand_rp/) printf "%s%s%s ", "'$red'", $i, "'$reset'"; else if ($i ~ /cand_bootstrap_router/) printf "%s%s%s ", "'$green'", $i, "'$reset'"; else printf "%s ", $i} printf "\n"}'
    echo -e "=================================================" # Add an equal sign separator
  done
  echo -e "=================================================\n" # Add an equal sign separator
}