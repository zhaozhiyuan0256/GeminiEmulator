import copy
from abc import abstractmethod


class Router:
    """
    Router class for providing path computation services between nodes in an undirected graph.
    """

    def __init__(self, adj_list: list, adj_matrix: list):
        """
        Initialize the Router with adjacency list and adjacency matrix.

        adj_list:
            A 2D array representing the adjacency list of an undirected graph.
            Each element is a list of nodes that are adjacent to the corresponding node.
            Example: [[adjacent_nodes_of_node_0], [adjacent_nodes_of_node_1], ...]

        adj_matrix:
            A 2D array representing the adjacency matrix of an undirected graph.
            Each element [i][j] is the distance (or weight) from node i to node j.
            Example: [[distances_from_node_0_to_all_nodes], [distances_from_node_1_to_all_nodes], ...]
        """
        try:
            self._validate_adj_list_and_matrix(adj_list, adj_matrix)
            self.node_count = len(adj_list)
            self.adj_list = copy.deepcopy(adj_list)
            self.adj_matrix = copy.deepcopy(adj_matrix)
            self.predecessor_matrix = [
                [-1] * self.node_count for _ in range(self.node_count)
            ]
        except ValueError as e:
            raise

    def modify_adj_list(self, adj_list: list):
        if len(adj_list) != self.node_count:
            raise ValueError(
                "The length of the new adj_list must be the same as the old one."
            )
        if not isinstance(adj_list, list) or not all(
            isinstance(row, list) for row in adj_list
        ):
            raise ValueError("adj_list must be a 2D array (list of lists).")
        self.adj_list = copy.deepcopy(adj_list)

    def modify_adj_matrix(self, adj_matrix: list):
        if len(adj_matrix) != self.node_count:
            raise ValueError(
                "The length of the new adj_matrix must be the same as the old one."
            )
        if not isinstance(adj_matrix, list) or not all(
            isinstance(row, list) for row in adj_matrix
        ):
            raise ValueError("adj_matrix must be a 2D array (list of lists).")

        if not all(len(row) == len(adj_matrix) for row in adj_matrix):
            raise ValueError(
                "Each row in adj_matrix must have the same length as the number of columns."
            )

        self.adj_matrix = copy.deepcopy(adj_matrix)

    def modify_adj_list_and_matrix(self, adj_list: list, adj_matrix: list):
        self.modify_adj_list(adj_list)
        self.modify_adj_matrix(adj_matrix)
        self.reset_predecessor_matrix()

    def reset_predecessor_matrix(self):
        self.predecessor_matrix = [
            [-1] * self.node_count for _ in range(self.node_count)
        ]

    def print_adj_list(self):
        print("Router.adj_list:")
        for i in range(self.node_count):
            print(i, ": ", self.adj_list[i])

    def print_adj_matrix(self):
        print("Router.adj_matrix:")
        for i in range(self.node_count):
            print(self.adj_matrix[i])

    def print_predecessor_matrix(self):
        print("Router.predecessor_matrix:")
        for i in range(self.node_count):
            print(self.predecessor_matrix[i])

    @abstractmethod
    def calculate_adj_matrix_and_predecessor_matrix(self):
        pass

    def get_next_from_src_to_dst(self, src, dst):
        return self.predecessor_matrix[src][dst]

    def get_next_from_src_to_all(self, src):
        nexts = {}
        for i in range(self.node_count):
            nexts[i] = self.predecessor_matrix[src][i]
        return nexts

    def get_distance_from_src_to_dst(self, src, dst):
        return self.adj_matrix[src][dst]

    def get_distance_from_src_to_all(self, src):
        distances = {}
        for i in range(self.node_count):
            distances[i] = self.get_distance_from_src_to_dst(src, i)
        return distances

    def get_path_from_src_to_dst(self, src, dst):
        path = []
        node = src
        while node != dst:
            path.append(node)
            node = self.get_next_from_src_to_dst(node, dst)
        path.append(dst)
        return path

    def get_path_from_src_to_all(self, src):
        paths = {}
        for i in range(self.node_count):
            paths[i] = self.get_path_from_src_to_dst(src, i)
        return paths

    def _validate_adj_list_and_matrix(self, adj_list, adj_matrix):
        if not (
            isinstance(adj_list, list)
            and all(isinstance(row, list) for row in adj_list)
        ):
            raise ValueError("adj_list must be a list of lists.")
        if not (
            isinstance(adj_matrix, list)
            and all(isinstance(row, list) for row in adj_matrix)
        ):
            raise ValueError("adj_matrix must be a list of lists.")

        if len(adj_list) != len(adj_matrix):
            raise ValueError("The lengths of adj_list and adj_matrix must be the same.")

        if not all(len(row) == len(adj_matrix) for row in adj_matrix):
            raise ValueError(
                "Each row in adj_matrix must have the same length as the number of columns."
            )


class FloydRouter(Router):
    def __init__(self, adj_list, adj_matrix):
        super().__init__(adj_list, adj_matrix)

    def calculate_adj_matrix_and_predecessor_matrix(self):
        for i in range(self.node_count):
            self.predecessor_matrix[i][i] = i
            for neighbor in self.adj_list[i]:
                self.predecessor_matrix[i][neighbor] = neighbor
        for i in range(self.node_count):
            for j in range(self.node_count):
                for k in range(self.node_count):
                    if (
                        self.adj_matrix[i][k] + self.adj_matrix[k][j]
                        < self.adj_matrix[i][j]
                    ):
                        self.adj_matrix[i][j] = (
                            self.adj_matrix[i][k] + self.adj_matrix[k][j]
                        )
                        self.predecessor_matrix[i][j] = self.predecessor_matrix[i][k]
