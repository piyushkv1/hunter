import argparse
import requests
import json

# LoadBalancer serivce ID
LBS_ID = "0cc78196-3991-4307-84e9-fb3631380143"

# NSX Client Cert
cert = "certificates/client.crt"
key = "certificates/client.key"
CERT = (cert, key)

HEADERS = {'content-type': 'application/json'}

# NSX manager ip
base_url = "https://10.192.163.144/"

# Number of server pool needs to create
POOL_NUMBER = 10


def _get_call(url):
    return requests.get(url, headers=HEADERS, cert=CERT, verify=False)


def _post_call(url, body):
    return requests.post(url, data=json.dumps(body), headers=HEADERS, cert=CERT, verify=False)


def _put_call(url, body):
    return requests.put(url, data=json.dumps(body), headers=HEADERS, cert=CERT, verify=False)


def _delete(url):
    r = requests.delete(url, headers={'X-Allow-Overwrite': 'true'}, cert=CERT, verify=False)


def attach_vs_to_lbs(vs_id):
    url = base_url + "api/v1/loadbalancer/services/" + LBS_ID
    lbs = json.loads(_get_call(url).text)
    assert lbs['id'] == LBS_ID
    lbs['virtual_server_ids'] += [vs_id]
    assert vs_id in lbs['virtual_server_ids']
    r = _put_call(url, lbs)
    print r.text


def dettach_vs_from_lbs():
    vs_id = find_test_vs()
    url = base_url + "api/v1/loadbalancer/services/" + LBS_ID
    lbs = json.loads(_get_call(url).text)
    assert lbs['id'] == LBS_ID
    lbs['virtual_server_ids'].remove(vs_id)
    assert vs_id not in lbs['virtual_server_ids']
    r = _put_call(url, lbs)
    return vs_id


def delete_virtual_server(vs_id):
    url = base_url + "api/v1/loadbalancer/virtual-servers/" + vs_id
    vs = json.loads(_get_call(url).text)
    _delete(url)
    for rule_id in vs['rule_ids']:
        lb_rule_url = base_url + "api/v1/loadbalancer/rules/" + rule_id
        lb_rule = json.loads(_get_call(lb_rule_url).text)
        related_pool = lb_rule['actions'][0]['pool_id']
        _delete(lb_rule_url)
        related_pool_url = base_url + "api/v1/loadbalancer/pools/" + related_pool
        _delete(related_pool_url)


def find_test_vs():
    url = base_url + "api/v1/loadbalancer/virtual-servers"
    r = _get_call(url)
    for vs in json.loads(r.text)['results']:
        if vs['display_name'] == "test_vs_pool_limit":
            return vs['id']


def create_virtual_server_with_lb_rules(lb_rules):
    url = base_url + "api/v1/loadbalancer/virtual-servers?action=create_with_rules"
    body = {
        "virtual_server": {
            "ip_protocol": "TCP",
            "enabled": "true",
            "application_profile_id": "cb2d0721-cc15-5b8e-8633-14be114eac5e",
            "ip_address": "4.4.0.200",
            "port": "80",
            "display_name": "test_vs_pool_limit",
            "description": "LB_HTTP_VirtualServer for testing LBS virtual server limit exceed"
        },
        "rules": lb_rules
    }
    r = _post_call(url, body)
    return json.loads(r.text)['virtual_server']['id']


def create_lb_rule(pool_id, pool_name):
    url = base_url + "api/v1/loadbalancer/rules"
    body = {
        "match_conditions": [{
            "method": "GET",
            "type": "LbHttpRequestMethodCondition",
            "inverse": False}],
        "match_strategy": "ALL",
        "phase": "HTTP_FORWARDING",
        "actions": [{
            "pool_id": pool_id,
            "type": "LbSelectPoolAction"}],
        "resource_type": "LbRule",
        "display_name": "test_nsxerror_" + pool_name
    }
    r = _post_call(url, body)
    return json.loads(r.text)


def create_pool_api(pool_name):
    url = base_url + "api/v1/loadbalancer/pools"
    body = {
        "algorithm": "ROUND_ROBIN",
        "tcp_multiplexing_number": 6,
        "tcp_multiplexing_enabled": "false",
        "min_active_members": 1,
        "display_name": pool_name,
        "description": ""
    }
    r = _post_call(url, body)
    return json.loads(r.text)


def get_existing_pools():
    existing_pools = {}
    url = base_url + "api/v1/loadbalancer/pools/"
    r = _get_call(url)
    for pool in json.loads(r.text)['results']:
        existing_pools.update({pool['display_name']: pool})
    return existing_pools


def create_lb_pool_and_rule(pool_number):
    lb_rules = []
    existing_pools = get_existing_pools()
    for x in range(0, pool_number):
        pool_name = 'test_pool%s' % (x)
        if pool_name not in existing_pools:
            pool = create_pool_api(pool_name)
        else:
            pool = existing_pools[pool_name]
        lb_rule = create_lb_rule(pool['id'], pool_name)
        lb_rules.append(lb_rule)
    return lb_rules


def main():
    get_existing_pools()
    return
    lb_rules = create_lb_pool_and_rule(POOL_NUMBER)
    # print lb_rules
    vs_id = create_virtual_server_with_lb_rules(lb_rules)
    # print vs_id
    attach_vs_to_lbs(vs_id)


def tear_down():
    vs_id = dettach_vs_from_lbs()
    delete_virtual_server(vs_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true",
                        help="Tear down the test set ups")
    args = parser.parse_args()

    if args.delete:
        tear_down()
    else:
        main()