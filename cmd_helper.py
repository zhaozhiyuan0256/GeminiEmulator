import socket


class CmdHelper:
    def __init__(self):
        pass

    @staticmethod
    def reset_ovs_environment():
        cmd = "ovs-ofctl del-flows br0 && systemctl restart openvswitch-switch"
        return cmd

    @staticmethod
    def allow_connection_flow_through_ovs(ip, port):
        cmd = "ovs-ofctl add-flow br0 tcp,in_port=1,tcp_dst=22,nw_dst={},actions=output:{}".format(
            ip, port
        )

    @staticmethod
    def set_ovs_flow(src_ovs_port, src_ip, dst_ip, nxt_ovs_port, nxt_mac):
        if nxt_mac == "":
            cmd = "ovs-ofctl add-flow br0 ip,in_port={},nw_src={},nw_dst={},actions=output:{};".format(
                src_ovs_port, src_ip, dst_ip, nxt_ovs_port
            )
        else:
            cmd = "ovs-ofctl add-flow br0 ip,in_port={},nw_src={},nw_dst={},actions=mod_dl_dst:{},output:{};".format(
                src_ovs_port, src_ip, dst_ip, nxt_mac, nxt_ovs_port
            )

    @staticmethod
    def clean_tc_environment():
        cmd = "tc qdisc del dev enp1s0 root"
        return cmd

    @staticmethod
    def init_tc_environment(nic_name):
        cmd1 = "tc qdisc add dev {} root handle 1: htb".format(nic_name)
        cmd2 = "tc class add dev {} parent 1: classid 1:1 htb rate 50mbit".format(
            nic_name
        )
        return cmd1 + ";" + cmd2

    @staticmethod
    def add_tc_queue_delay(nic_name, index, delay_time):
        cmd1 = "tc class add dev {} parent 1:1 classid 1:{}0 htb rate 10mbit".format(
            nic_name, str(index)
        )
        cmd2 = "tc qdisc add dev {} parent 1:{}0 netem delay {}ms".format(
            nic_name, str(index), str(delay_time)
        )
        return cmd1 + ";" + cmd2

    @staticmethod
    def modify_tc_queue_delay(nic_name, index, delay_time):
        cmd = "tc qdisc change dev {} parent 1:{}0 netem delay {}ms".format(
            nic_name, str(index), str(delay_time)
        )
        return cmd

    @staticmethod
    def set_tc_filter(dst, index):
        dst_16 = socket.inet_aton(dst).hex()
        cmd = (
            'tc filter del dev enp1s0 parent 1: prio 1 handle $(tc filter list dev enp1s0 | grep -B1 "{}" | '
            "head -1 |  awk '{{print $12}}') u32 ; tc filter"
            " add dev enp1s0 protocol ip parent 1: prio 1 u32 match ip dst {} flowid 1:{}0"
        ).format(dst_16, dst, index)
        return cmd
