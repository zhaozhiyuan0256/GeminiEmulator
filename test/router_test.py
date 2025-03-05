import sys
import os
from math import inf

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from router import FloydRouter

if __name__ == "__main__":
    adj_list = [[1], [0, 2], [1, 3], [2]]
    adj_matrix = [
        [0, 8, inf, inf],
        [8, 0, 8, inf],
        [inf, 8, 0, 8],
        [inf, inf, 8, 0],
    ]
    fr = FloydRouter(adj_list, adj_matrix)
    fr.calculate_adj_matrix_and_predecessor_matrix()
    fr.print_adj_matrix()
    fr.print_predecessor_matrix()

    print(fr.get_path_from_src_to_dst(0, 0))
    print(fr.get_distance_from_src_to_dst(0, 3))
    print(fr.get_path_from_src_to_all(0))
    print(fr.get_next_from_src_to_all(0))
