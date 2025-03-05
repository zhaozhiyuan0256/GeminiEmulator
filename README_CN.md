# GEMINI

## 代码结构
``` txt
程序入口：
main.py

主要类：
constellation_system.py         仿真执行模块
  |__class ConstellationSystem
topology.py                     拓扑维护模块
  |__class Topology       
cluster_instance.py             设备(宿主机、kvm)交互模块
  |__class ClusterInstance


工具类：
|__node.py                      存储邻接节点信息（方向、名称、时延）
    |__class BaseNode
    |__class SatNode
    |__class FacilityNode
|__router.py                    路径计算
    |__class Router
    |__class FloydRouter
|__host.py                      主机连接与命令执行
    |__class Host
|__cmd_helper.py                命令构建
    |__class CmdHelper
```

## 命名规范
``` txt
python源文件：src_name.py
类名：        ClassName
函数名：      function_name
变量名：      var_name
常量名：      CONST_VALUE_NAME
```

## 流程说明

### 入口文件 main.py
```python
from constellation_system import ConstellationSystem

# 星座的标准TLE文件，其中卫星命名必须为“星座名称-编号”，例如gemini-1
TLES_FILEPATH = "./data/three.tle" 

# 地面设备的描述json文件，键名为“设备类型-编号”，例如core-1，内容包含设备类型、经度信息、纬度信息
FACILITIES_FILEPATH = "./data/facilities.json" 

# 描述星座的星间链路的文件，此处设定卫星部分拓扑形状不变，每一行用于描述一个单向的星间链路，格式为“起始卫星 方向 结束卫星”
ISLS_FILEPATH = "./data/three.isls" 

# 描述宿主机和虚拟机设备信息的json文件，用于实际进行SSH连接的建立、ovs和tc规则的生成和执行
HOSTS_FILEPATH = "./data/hosts.json" 

# 更新拓扑以及ovs、tc规则的时间周期
UPDATE_INTERVAL = 100

# 如果设置DEBUG模式为True时，命令不会真实执行，只会打印到命令行
DEBUG_MODE = True

if __name__ == "__main__":
    cs = ConstellationSystem(
        TLES_FILEPATH,
        FACILITIES_FILEPATH,
        ISLS_FILEPATH,
        HOSTS_FILEPATH,
        UPDATE_INTERVAL,
        DEBUG_MODE,
    )
    cs.run()
```

### 流程执行 ConstellationSystem
```python
class ConstellationSystem:
    # 初始化过程
    def __init__(
        self,
        tles_filepath,
        facilities_filepath,
        isls_filepath,
        hosts_filepath,
        update_interval,
        debug_mode,
    ):
        # 初始化拓扑类
        self.topology = Topology(tles_filepath, facilities_filepath, isls_filepath)
        # 初始化集群实例类
        self.cluster_instance = ClusterInstance(hosts_filepath, debug_mode)
        # 设置更新周期
        self.update_interval = update_interval

    # 运行入口
    def run(self):
        # 实例连接
        self.cluster_instance.connect()
        # 准备实例网络环境（包括清空ovs规则、清空tc规则、为每个虚拟机建立初始化的tc队列）
        self.cluster_instance.prepare_cluster_environment()
        try:
            while True:
                current_utc_time = datetime.now(timezone.utc)
                print(f"[INFO] Current time: {current_utc_time}")
                # 根据时间信息更新拓扑状态
                self.topology.update_topology_by_time(current_utc_time)
                # 主要信息1，拓扑更新后的邻接节点关系
                neighbor_dict = self.topology.get_neighbor_dict()
                # 主要信息2，拓扑更新后的所有节点对间路径
                all_pair_path_dict = self.topology.get_all_pair_path_dict()
                # 集群实例类根据上述信息更新ovs和tc规则
                self.cluster_instance.update_network_status_by_topology(
                    neighbor_dict, all_pair_path_dict
                )
                # 暂停，直到时间走完一个更新周期
                self.sleep_for_interval(current_utc_time)
        except KeyboardInterrupt:
            # 程序退出时的清理工作，主要是清空ovs和tc规则，断开SSH连接
            self.cleanup()

    def sleep_for_interval(self, last_utc_time):
        current_utc_time = datetime.now(timezone.utc)
        time_difference = current_utc_time - last_utc_time
        if time_difference.total_seconds() < self.update_interval:
            time.sleep(self.update_interval - time_difference.total_seconds())
        else:
            print(
                "[WARN] The update interval is shorter than the actual execution time. It needs to be longer."
            )

    def cleanup(self):
        print("[INFO] Program interrupted. Executing cleanup logic.")
        self.cluster_instance.cleanup()
```