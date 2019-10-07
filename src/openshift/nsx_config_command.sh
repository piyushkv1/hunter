python /nsx_config.py --cert '' --mp 10.116.249.88 --k8scluster oc-cluster --edge_cluster edge-cluster \
--tz overlay-tz --t0 oc-t0-router --pod_ipblock_name oc-pod-ipblock --pod_ipblock_cidr 172.31.0.0/16 \
--snat_ipblock_name oc-snat-ipblock --snat_ipblock_cidr 192.168.0.0/16 \
--node admin.rhel.osmaster,admin.rhel.osnode1,admin.rhel.osnode2 --node_ls node-ls --node_lr oc-node-t1-lr \
--node_network_cidr '172.20.2.0/16' --vc_host 10.116.248.50 --vc_user 'administrator@vsphere.local' \
--vc_password 'Admin!23' \
--vms 1-containerhost_k8snode-rhel74-v9-local-1818,2-containerhost_k8snode-rhel74-v9-local-1818,3-containerhost_k8snode-rhel74-v9-local-1818