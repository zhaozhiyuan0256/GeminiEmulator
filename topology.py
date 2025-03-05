from skyfield.api import load, wgs84
from datetime import datetime, timezone
import json
from math import inf

from node import SatNode, FacilityNode
from router import FloydRouter

MIN_ELEVATION = 0  # Minimum Elevation Angle for Determining Whether Ground Facilities Can Establish a Connection with Satellites
SPEED_OF_LIGHT = 299792458  # Speed of Light, Unit: m/s


class Topology:
    def __init__(self, tles_filepath, facilities_filepath, isls_filepath):
        self.satellite_dict = self._load_tle(tles_filepath)
        self.facility_dict = self._load_facilities(facilities_filepath)

        # Total Number of Nodes, Including Satellite Nodes and Ground Facility Nodes
        self.node_count = len(self.satellite_dict) + len(self.facility_dict)

        # The node name corresponds one-to-one with the node index, with satellites listed first and ground facilities following.
        self.node_list = list()

        # The node name corresponds one-to-one with the node class (satellite node or facility node), and the node class actually stores the names of adjacent nodes and their latency information.
        self.node_dict = dict()

        # The topology adjacency matrix, where the indices align with the node_list, stores the latency information between nodes.
        self.adj_matrix = self.init_adj_matrix(self.node_count)
        self.init_topology(isls_filepath)
        self.adj_list = self.init_adj_list(self.adj_matrix)

        self.router = self.init_router()
        # self.print_node_dict()
        # self.print_adj_matrix()

    def init_adj_matrix(self, node_count):
        """
        Initialize the Adjacency Matrix Based on the Number of Nodes: All elements are set to "inf" except for the diagonal elements, which are set to 0.
        """
        adj_matrix = [[inf] * node_count for i in range(node_count)]
        for i in range(0, node_count):
            adj_matrix[i][i] = 0
        return adj_matrix

    def init_adj_list(self, adj_matrix):
        """
        Update the Adjacency List Based on the Adjacency Matrix: Ensure the call sequence is reasonable — before the update, the adjacency matrix only describes the direct connection information in a two-dimensional matrix.
        """
        adj_list = [[] for _ in range(self.node_count)]
        for i in range(self.node_count):
            for j in range(self.node_count):
                if adj_matrix[i][j] != 0 and adj_matrix[i][j] != inf:
                    adj_list[i].append(j)
        return adj_list

    def init_topology(self, isls_filepath):
        """
        Initialize the Topology Based on the ISLs File:
        Assume the reference time is 00:00 on January 1, 2025.
        The main initialization tasks include:

        1. Create node_list: A string array used to store node name information.
        2. Create node_dict: A node dictionary where the key is the node name and the value is the node object (SatNode or FacilityNode). It stores information about adjacent nodes, including relative position, name, and delay.
           All delays are initialized based on the reference time.
           Satellite-to-ground connection relationships are defined according to the reference time.
        """
        init_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        ts = load.timescale()
        skyfield_time = ts.utc(init_time)

        # Fill the node_list, init the keys of node_dict
        for sat_name in self.satellite_dict:
            self.node_list.append(sat_name)
            self.node_dict[sat_name] = SatNode()
        for facility_name in self.facility_dict:
            self.node_list.append(facility_name)
            self.node_dict[facility_name] = FacilityNode()

        # Fill the node_dict and the delay between satellites in adj_matrix
        with open(isls_filepath, "r") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip("\n").split(" ")
            first_sat_name = line[0]
            relative_position = line[1]
            second_sat_name = line[2]
            first_sat_in_node_list_index = self.node_list.index(first_sat_name)
            second_sat_in_node_list_index = self.node_list.index(second_sat_name)
            delay_between_two_satellites = self.get_delay_between_two_satellites(
                first_sat_name, second_sat_name, skyfield_time
            )
            setattr(
                self.node_dict[first_sat_name],
                relative_position + "_neighbor_info",
                [
                    second_sat_name,
                    delay_between_two_satellites,
                ],
            )
            self.adj_matrix[first_sat_in_node_list_index][
                second_sat_in_node_list_index
            ] = delay_between_two_satellites
            self.adj_matrix[second_sat_in_node_list_index][
                first_sat_in_node_list_index
            ] = delay_between_two_satellites

        # Find the neighbor sat of ground facilities, modify the self.node_dict of sat and facility, modify the adj_matrix
        for facility_name in self.facility_dict:
            self.update_facility_node_info_by_skyfield_time(
                facility_name, skyfield_time
            )

    def init_router(self):
        """
        Return the Router Calculator Based on the Adjacency List and Adjacency Matrix
        """
        return FloydRouter(self.adj_list, self.adj_matrix)

    def update_topology_by_time(self, utc_time):
        """
        Change the Topology Based on the Input Time
        """
        ts = load.timescale()
        skyfield_time = ts.utc(utc_time)

        # Reset the adj_matrix
        self.adj_matrix = self.init_adj_matrix(self.node_count)
        # Update delay between satellites, modify the self.node_dict and the adj_matrix
        for sat_name in self.satellite_dict:
            self.update_sat_node_info_by_skyfield_time(sat_name, skyfield_time)

        # Update delay between facilities and satellites, modify the self.node_dict and the adj_matrix
        for facility_name in self.facility_dict:
            self.update_facility_node_info_by_skyfield_time(
                facility_name, skyfield_time
            )
        self.adj_list = self.init_adj_list(self.adj_matrix)
        # Router Calculator Supports Modifying the Adjacency Matrix and Adjacency List
        self.router.modify_adj_list_and_matrix(self.adj_list, self.adj_matrix)

    def update_sat_node_info_by_skyfield_time(self, sat_name, skyfield_time):
        """
        Update the Delay Information Between Satellites and Their Adjacent Nodes Based on the Reference Time
        """
        sat_up_neighbor_name = self.node_dict[sat_name].up_neighbor_info[0]
        sat_down_neighbor_name = self.node_dict[sat_name].down_neighbor_info[0]
        sat_left_neighbor_name = self.node_dict[sat_name].left_neighbor_info[0]
        sat_right_neighbor_name = self.node_dict[sat_name].right_neighbor_info[0]
        self.node_dict[sat_name].ground_neighbor_info = None

        sat_index_in_node_list = self.node_list.index(sat_name)
        sat_up_neighbor_index_in_node_list = self.node_list.index(sat_up_neighbor_name)
        sat_down_neighbor_index_in_node_list = self.node_list.index(
            sat_down_neighbor_name
        )
        sat_left_neighbor_index_in_node_list = self.node_list.index(
            sat_left_neighbor_name
        )
        sat_right_neighbor_index_in_node_list = self.node_list.index(
            sat_right_neighbor_name
        )

        delay_between_sat_and_up_neighbor = self.get_delay_between_two_satellites(
            sat_name, sat_up_neighbor_name, skyfield_time
        )
        delay_between_sat_and_down_neighbor = self.get_delay_between_two_satellites(
            sat_name, sat_down_neighbor_name, skyfield_time
        )
        delay_between_sat_and_left_neighbor = self.get_delay_between_two_satellites(
            sat_name, sat_left_neighbor_name, skyfield_time
        )
        delay_between_sat_and_right_neighbor = self.get_delay_between_two_satellites(
            sat_name, sat_right_neighbor_name, skyfield_time
        )

        # update the self.node_dict
        self.node_dict[sat_name].up_neighbor_info[1] = delay_between_sat_and_up_neighbor
        self.node_dict[sat_name].down_neighbor_info[
            1
        ] = delay_between_sat_and_down_neighbor
        self.node_dict[sat_name].left_neighbor_info[
            1
        ] = delay_between_sat_and_left_neighbor
        self.node_dict[sat_name].right_neighbor_info[
            1
        ] = delay_between_sat_and_right_neighbor

        # update the self.adj_matrix
        self.adj_matrix[sat_index_in_node_list][
            sat_up_neighbor_index_in_node_list
        ] = delay_between_sat_and_up_neighbor
        self.adj_matrix[sat_index_in_node_list][
            sat_down_neighbor_index_in_node_list
        ] = delay_between_sat_and_down_neighbor
        self.adj_matrix[sat_index_in_node_list][
            sat_left_neighbor_index_in_node_list
        ] = delay_between_sat_and_left_neighbor
        self.adj_matrix[sat_index_in_node_list][
            sat_right_neighbor_index_in_node_list
        ] = delay_between_sat_and_right_neighbor

        self.adj_matrix[sat_up_neighbor_index_in_node_list][
            sat_index_in_node_list
        ] = delay_between_sat_and_up_neighbor
        self.adj_matrix[sat_down_neighbor_index_in_node_list][
            sat_index_in_node_list
        ] = delay_between_sat_and_down_neighbor
        self.adj_matrix[sat_left_neighbor_index_in_node_list][
            sat_index_in_node_list
        ] = delay_between_sat_and_left_neighbor
        self.adj_matrix[sat_right_neighbor_index_in_node_list][
            sat_index_in_node_list
        ] = delay_between_sat_and_right_neighbor

    def update_facility_node_info_by_skyfield_time(self, facility_name, skyfield_time):
        """
        Calculate the Direct Adjacency Relationship Between Satellites and Ground Facilities Based on the Reference Time
        """
        neighbor_sat_name, delay_between_facility_and_satellite = (
            self.get_neighbor_sat_of_facility(facility_name, skyfield_time)
        )
        facility_in_node_list_index = self.node_list.index(facility_name)
        neighbor_sat_in_node_list_index = self.node_list.index(neighbor_sat_name)
        setattr(
            self.node_dict[facility_name],
            "sat_neighbor_info",
            (
                neighbor_sat_name,
                delay_between_facility_and_satellite,
            ),
        )
        current_ground_neighbor_info = getattr(
            self.node_dict[neighbor_sat_name], "ground_neighbor_info", []
        )
        if current_ground_neighbor_info is None:
            current_ground_neighbor_info = []
        current_ground_neighbor_info.append(
            (facility_name, delay_between_facility_and_satellite)
        )
        setattr(
            self.node_dict[neighbor_sat_name],
            "ground_neighbor_info",
            current_ground_neighbor_info,
        )
        self.adj_matrix[facility_in_node_list_index][
            neighbor_sat_in_node_list_index
        ] = delay_between_facility_and_satellite
        self.adj_matrix[neighbor_sat_in_node_list_index][
            facility_in_node_list_index
        ] = delay_between_facility_and_satellite

    def get_neighbor_dict(self):
        """
        Update node_dict and adj_matrix.
        Return information about adjacent nodes in the format specified in /doc/example.json.
        """
        return {
            node_name: self.node_dict[node_name].get_all_attributes()
            for node_name in self.node_dict
        }

    def get_all_pair_path_dict(self):
        """
        Return the shortest path information between all pairs of nodes
        Return information in the format specified in /doc/example.json.
        """
        all_pair_path_dict = {}
        self.router.calculate_adj_matrix_and_predecessor_matrix()
        for src_index in range(self.node_count):
            all_pair_path_dict[self.node_list[src_index]] = {}
            route_from_src_index_to_all_dst_index = (
                self.router.get_path_from_src_to_all(src_index)
            )
            for dst_index in route_from_src_index_to_all_dst_index:
                all_pair_path_dict[self.node_list[src_index]][
                    self.node_list[dst_index]
                ] = [
                    self.node_list[cur_index]
                    for cur_index in route_from_src_index_to_all_dst_index[dst_index]
                ]
        return all_pair_path_dict

    def _load_tle(self, tles_filepath):
        """
        Use Skyfield’s load Function to Load TLE Files:
        Returns a dictionary where the key is the satellite name and the value is an EarthSatellite object.
        """
        satellite_list = load.tle_file(tles_filepath)
        satellite_dict = {satellite.name: satellite for satellite in satellite_list}
        return satellite_dict

    def _load_facilities(self, facilities_filepath):
        """
        Use the wgs84.latlon Function to Create GeographicPosition Objects for Ground Facilities:
        Returns a dictionary where the key is the facility name and the value is a GeographicPosition object.
        """
        with open(facilities_filepath, "r") as f:
            data = json.load(f)
        facility_dict = {
            facility_name: wgs84.latlon(
                latitude_degrees=facility_info["latitude"],
                longitude_degrees=facility_info["longitude"],
                elevation_m=0,
            )
            for facility_name, facility_info in data.items()
        }
        return facility_dict

    def get_distance_between_two_satellites(self, sat1_name, sat2_name, skyfield_time):
        position1 = self.satellite_dict[sat1_name].at(skyfield_time)
        position2 = self.satellite_dict[sat2_name].at(skyfield_time)
        return float((position2 - position1).distance().km)

    def get_delay_between_two_satellites(self, sat1_name, sat2_name, skyfield_time):
        return self.distance_km_to_light_travel_time_ms(
            self.get_distance_between_two_satellites(
                sat1_name, sat2_name, skyfield_time
            )
        )

    def get_elevation_between_facility_and_satellite(
        self, facility_name, satellite_name, skyfield_time
    ):
        satellite = self.satellite_dict[satellite_name]
        facility = self.facility_dict[facility_name]
        difference = satellite - facility
        alt_degree, _, _ = difference.at(skyfield_time).altaz()
        return alt_degree.degrees

    def get_distance_between_facility_and_satellite(
        self, facility_name, satellite_name, skyfield_time
    ):
        satellite = self.satellite_dict[satellite_name]
        facility = self.facility_dict[facility_name]
        difference = satellite - facility
        _, _, distance = difference.at(skyfield_time).altaz()
        return float(distance.km)

    def get_delay_between_facility_and_satellite(
        self, facility_name, satellite_name, skyfield_time
    ):
        return self.distance_km_to_light_travel_time_ms(
            self.get_distance_between_facility_and_satellite(
                facility_name, satellite_name, skyfield_time
            )
        )

    def distance_km_to_light_travel_time_ms(self, distance_km):
        return distance_km * 1000 / SPEED_OF_LIGHT * 1000

    def get_neighbor_sat_of_facility(self, facility_name, skyfield_time):
        """
        Return the Access Satellite Based on the Facility Name and Reference Time:
        Only select the nearest satellite within the visible range.
        """
        candidate_sat_name = None
        candidate_sat_facility_delay = inf
        for sat_name in self.satellite_dict:
            if (
                self.get_elevation_between_facility_and_satellite(
                    facility_name, sat_name, skyfield_time
                )
                >= MIN_ELEVATION
            ):
                current_sat_facility_delay = (
                    self.get_distance_between_facility_and_satellite(
                        facility_name, sat_name, skyfield_time
                    )
                )
                if current_sat_facility_delay < candidate_sat_facility_delay:
                    candidate_sat_facility_delay = current_sat_facility_delay
                    candidate_sat_name = sat_name
        return candidate_sat_name, self.get_delay_between_facility_and_satellite(
            facility_name, candidate_sat_name, skyfield_time
        )

    def print_node_dict(self):
        print("[INFO][NODE_DICT]")
        for node_name in self.node_dict:
            print(node_name, ":", self.node_dict[node_name])

    def print_adj_matrix(self):
        print("[INFO][ADJ_MATRIX]")
        col_headers = [f"{0:>3}"] + [f"{i:>10}" for i in range(len(self.adj_matrix))]
        print(" ".join(col_headers))

        for i, row in enumerate(self.adj_matrix):
            formatted_row = [f"{i:>3}"] + [
                f"{value:>10.3f}" if value != float("inf") else f"{'inf':>10}"
                for value in row
            ]
            print(" ".join(formatted_row))


if __name__ == "__main__":
    # topology = Topology(
    #     "./data/three.tle", "./data/facilities.json", "./data/three.isls"
    # )
    # current_utc_time = datetime.now(timezone.utc)
    # topology.update_topology_by_time(current_utc_time)
    # print(json.dumps(topology.get_neighbor_dict()))
    # print(json.dumps(topology.get_all_pair_path_dict()))
    pass
