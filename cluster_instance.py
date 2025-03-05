import json

from host import Host
from cmd_helper import CmdHelper

from enum import Enum


class SatNeighborType(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    GROUND = 5


class FacilityNeighborType(Enum):
    SAT = 1


class ClusterInstance:
    def __init__(self, hosts_filepath, debug_mode):
        self.host_instance_dict = self._load_host_instances(hosts_filepath)
        self.debug_mode = debug_mode

    def _load_host_instances(self, hosts_filepath):
        """
        初始化Host类字典
        """
        host_instance_dict = {}
        with open(hosts_filepath, "r") as f:
            data = json.load(f)
        host_instance_dict = {
            host_name: Host(
                host_info["ip"],
                host_info["ssh_port"],
                host_info["username"],
                host_info["password"],
                type=host_info["type"],
                parent_host_name=(
                    host_info["parent_host_name"]
                    if "parent_host_name" in host_info
                    else None
                ),
                nic_name=host_info["nic_name"] if "nic_name" in host_info else None,
                ovs_port=host_info["ovs_port"] if "ovs_port" in host_info else None,
                mac_address=(
                    host_info["mac_address"] if "mac_address" in host_info else None
                ),
            )
            for host_name, host_info in data.items()
        }
        return host_instance_dict

    def connect(self):
        """
        执行SSH连接
        """
        for host_name in self.host_instance_dict:
            if not self.debug_mode:
                self.host_instance_dict[host_name].connect()
            print(f"[INFO] Connect to {host_name}.")

    def execute_cmd(self, host_name, cmd):
        """
        命令执行的统一入口
        """
        if not self.debug_mode:
            self.host_instance_dict[host_name].execute(cmd)
        print(f"[INFO] {host_name} execute:{cmd}")

    def prepare_cluster_environment(self):
        """
        准备集群环境，包括重置主机ovs或tc配置，放行SSH端口流量，初始化各虚拟机的tc队列
        """
        self.clean_host_environment()
        # Allow ssh traffic through ovs
        for host_name in self.host_instance_dict:
            self.execute_cmd(
                host_name,
                CmdHelper.allow_connection_flow_through_ovs(
                    self.host_instance_dict[host_name].host_ip,
                    self.host_instance_dict[host_name].ssh_port,
                ),
            )

        # Set basic tc queues of kvms
        self.set_basic_tc_queue_of_all_sats_and_facilities()

    def set_basic_tc_queue_of_all_sats_and_facilities(self):
        """
        初始化各虚拟机tc队列，如果是卫星，则配置5条队列，如果是地面设置，则仅配置1条队列
        """
        for host_name in self.host_instance_dict:
            if self.host_instance_dict[host_name].type in ["core", "ue", "sat"]:
                self.execute_cmd(
                    host_name,
                    CmdHelper.init_tc_environment(
                        self.host_instance_dict[host_name].nic_name
                    ),
                )
                if self.host_instance_dict[host_name].type == "sat":
                    self.execute_cmd(
                        host_name,
                        CmdHelper.add_tc_queue_delay(
                            self.host_instance_dict[host_name].nic_name,
                            SatNeighborType.UP,
                            0,
                        ),
                    )
                    self.execute_cmd(
                        host_name,
                        CmdHelper.add_tc_queue_delay(
                            self.host_instance_dict[host_name].nic_name,
                            SatNeighborType.DOWN,
                            0,
                        ),
                    )
                    self.execute_cmd(
                        host_name,
                        CmdHelper.add_tc_queue_delay(
                            self.host_instance_dict[host_name].nic_name,
                            SatNeighborType.LEFT,
                            0,
                        ),
                    )
                    self.execute_cmd(
                        host_name,
                        CmdHelper.add_tc_queue_delay(
                            self.host_instance_dict[host_name].nic_name,
                            SatNeighborType.RIGHT,
                            0,
                        ),
                    )
                    self.execute_cmd(
                        host_name,
                        CmdHelper.add_tc_queue_delay(
                            self.host_instance_dict[host_name].nic_name,
                            SatNeighborType.GROUND,
                            0,
                        ),
                    )
                elif self.host_instance_dict[host_name].type in ["core", "ue"]:
                    self.execute_cmd(
                        host_name,
                        CmdHelper.add_tc_queue_delay(
                            self.host_instance_dict[host_name].nic_name,
                            FacilityNeighborType.SAT,
                            0,
                        ),
                    )

    def clean_host_environment(self):
        """ 
        Clean ovs rules and tc rules
        """
        for host_name in self.host_instance_dict:
            if self.host_instance_dict[host_name].type == "host":
                self.execute_cmd(host_name, CmdHelper.reset_ovs_environment())
            elif self.host_instance_dict[host_name].type in ["core", "ue", "sat"]:
                self.execute_cmd(host_name, CmdHelper.clean_tc_environment())

    def set_all_tc_queue_delay_by_neighbor_dict(self, neighbor_dict):
        pass

    def set_ovs_rule_by_path(self, path):
        pass

    def set_all_ovs_rule_by_all_pair_path(self, all_pair_path_dict):
        pass

    def set_all_tc_filter_by_all_pair_path(self, all_pair_path_dict):
        pass

    def update_network_status_by_topology(self, neighbor_dict, all_pair_path_dict):
        """
        根据邻接列表和邻接矩阵更新ovs及tc规则，传入数据格式参考/doc/example.json
        """
        self.set_all_tc_queue_delay_by_neighbor_dict(neighbor_dict)
        self.set_all_ovs_rule_by_all_pair_path(all_pair_path_dict)
        self.set_all_tc_filter_by_all_pair_path(all_pair_path_dict)

    def disconnect_all(self):
        """
        关闭SSH连接
        """
        for host_name in self.host_instance_dict:
            if not self.debug_mode:
                self.host_instance_dict[host_name].close()
            print(f"[INFO] Close SSH connect with {host_name}.")


    def cleanup(self):
        """
        程序退出时，清空配置，断开SSH连接
        """
        if not self.debug_mode:
            print("[INFO] Clean the SSH environment")
            self.clean_host_environment()
            self.disconnect_all()