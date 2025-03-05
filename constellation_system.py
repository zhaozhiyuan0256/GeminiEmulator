from datetime import datetime, timezone
import time
from topology import Topology
from cluster_instance import ClusterInstance


class ConstellationSystem:
    def __init__(
        self,
        tles_filepath,
        facilities_filepath,
        isls_filepath,
        hosts_filepath,
        update_interval,
        debug_mode,
    ):
        self.topology = Topology(tles_filepath, facilities_filepath, isls_filepath)
        self.cluster_instance = ClusterInstance(hosts_filepath, debug_mode)
        self.update_interval = update_interval

    def run(self):
        self.cluster_instance.connect()
        self.cluster_instance.prepare_cluster_environment()
        try:
            while True:
                current_utc_time = datetime.now(timezone.utc)
                print(f"[INFO] Current time: {current_utc_time}")
                self.topology.update_topology_by_time(current_utc_time)
                neighbor_dict = self.topology.get_neighbor_dict()
                all_pair_path_dict = self.topology.get_all_pair_path_dict()
                self.cluster_instance.update_network_status_by_topology(
                    neighbor_dict, all_pair_path_dict
                )
                self.sleep_for_interval(current_utc_time)
        except KeyboardInterrupt:
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
