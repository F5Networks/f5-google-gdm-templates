#  expectValue = "Success"
#  expectFailValue = "Failure"
#  scriptTimeout = 1
#  replayEnabled = false

TMP_DIR='/tmp/<DEWPOINT JOB ID>'
STATE_FILE=${TMP_DIR}/state.json

# init temp dir
mkdir -p $TMP_DIR

# init test functions file
cat << 'EOF' > /tmp/<DEWPOINT JOB ID>/test_functions.sh
#/bin/bash

TMP_DIR=/tmp/<DEWPOINT JOB ID>
STATE_FILE=${TMP_DIR}/state.json

# usage: set_state foo bar
function set_state() {
    KEY="$1"
    VALUE="$2"

    # note: the > foo.tmp && mv foo.tmp foo below is hacky, but works for now
    cat ${STATE_FILE} | jq --arg arg1 "${KEY}" --arg arg2 "${VALUE}" '.[$arg1] = $arg2' > ${STATE_FILE}.tmp && mv ${STATE_FILE}.tmp ${STATE_FILE}
}

# usage: get_state foo
function get_state() {
    KEY="$1"

    RET=$(cat ${STATE_FILE} | jq --arg arg1 "${KEY}" '.[$arg1]' -r)
    echo $RET
}

# usage: get_ip ip offset
function get_ip() {
    ip=$(echo $1 | cut -d "/" -f 1)
    RET=$(echo $ip | awk -F. '{ printf "%d.%d.%d.%d", $1, $2, $3, $4+'$2' }')
    echo $RET
}

# usage: map string a:b,c:d
function map() {
    RET="$1"
    list=$(echo $2 | tr ',' ' ')
    for i in $list ; do
        kv=($(echo $i | tr ':' ' '))
        RET=$(echo $RET | sed "s/${kv[0]}/${kv[1]}/g")
    done
    echo $RET
}

# usage: get_mgmt_ip <instance> <zone> <public|private>
function get_mgmt_ip() {
    instance="$1"
    zone="$2"
    if [ -n "$3" ]; then
        ip_type="$3"
    else
        ip_type="public"
    fi

    output=$(gcloud compute instances describe ${instance} --zone=${zone} --format json)

    # different indexing for public vs. private
    if [[ $ip_type == "private" ]]; then
        echo $output | jq -r 'if (.networkInterfaces | length) > 1 then .networkInterfaces[1].networkIP else .networkInterfaces[0].networkIP end'
    else
        echo $output | jq -r '.networkInterfaces[].accessConfigs[]?|select (.name=="Management NAT")|.natIP'
    fi
}

# usage: get_app_ip <instance> <zone> <public|private>
function get_app_ip() {
    instance="$1"
    zone="$2"
    if [ -n "$3" ]; then
        ip_type="$3"
    else
        ip_type="public"
    fi

    output=$(gcloud compute instances describe ${instance} --zone=${zone} --format json)

    # different indexing for public vs. private
    if [[ $ip_type == "private" ]]; then
        echo $output | jq -r '.networkInterfaces[0].networkIP'
    else
        # 2nic, 3nic, etc. name is External NAT - 1nic is Management NAT
        nic_count=$(echo $output | jq -r '.networkInterfaces | length')
        if [[ $nic_count -eq 1 ]]; then
            echo $output | jq -r '.networkInterfaces[].accessConfigs[]?|select (.name=="Management NAT")|.natIP'
        else
            echo $output | jq -r '.networkInterfaces[].accessConfigs[]?|select (.name=="External NAT")|.natIP'
        fi
    fi
}

# usage: make_scp_request <host> <base> <file> <proxy_host>
function make_scp_request() {
    HOST="$1"
    BASE="$2"
    FILE="$3"
    PROXY_HOST="$4"

    if [ -n "$PROXY_HOST" ]; then
        response=$(scp -o "StrictHostKeyChecking=no" -o ConnectTimeout=10 -o "ProxyCommand ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 -i /etc/ssl/private/dewpt_private.pem dewpt@$PROXY_HOST -W %h:%p" -i /etc/ssl/private/dewpt_private.pem admin@${HOST}:$BASE$FILE /tmp/<DEWPOINT JOB ID>-${FILE})
    else
        response=$(scp -o "StrictHostKeyChecking=no" -o ConnectTimeout=8 -i /etc/ssl/private/dewpt_private.pem admin@${HOST}:$BASE$FILE /tmp/<DEWPOINT JOB ID>-${FILE})
    fi
    echo $response
}


# usage: make_ssh_request <host> <cmd> <proxy_host>
function make_ssh_request() {
    HOST="$1"
    CMD="$2"
    PROXY_HOST="$3"

    if [ -n "$PROXY_HOST" ]; then
        response=$(ssh -o "StrictHostKeyChecking=no" -o ConnectTimeout=5 -i /etc/ssl/private/dewpt_private.pem -o ProxyCommand="ssh -o 'StrictHostKeyChecking no' -o ConnectTimeout=7 -i /etc/ssl/private/dewpt_private.pem -W %h:%p dewpt@$PROXY_HOST" admin@"$HOST" "${CMD}")
    else
        response=$(ssh -o "StrictHostKeyChecking=no" -o ConnectTimeout=7 -i /etc/ssl/private/dewpt_private.pem admin@"$HOST" "${CMD}")
    fi
    echo $response
}

# usage: nc <host> <proxy_host>
function make_nc_request() {
    HOST="$1"
    PROXY_HOST="$2"
    CMD="nc -v -z -w 1 $HOST 22"
    if [ -n "$PROXY_HOST" ]; then
        response=$(ssh -o "StrictHostKeyChecking=no" -o ConnectTimeout=3 -i /etc/ssl/private/dewpt_private.pem dewpt@"$PROXY_HOST" "${CMD} 2>&1")
    else
        response=$(eval $CMD 2>&1)
    fi
    echo $response
}

# usage: get_env_public_ip
function get_env_public_ip() {
    # NOTE: specific source IP disabled for now as the corporate
    # network may change public IP's in the middle of a test
    #source_ip=$(curl https://ipecho.net/plain)
    #echo "'${source_ip}/32'"
    echo "0.0.0.0/0"
}
EOF

# init state file
echo '{}' > ${STATE_FILE}

echo "Success"
