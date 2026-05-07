#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from nav_msgs.msg import OccupancyGrid
from sensor_msgs_py import point_cloud2
import numpy as np
import traceback

from sonar_pipeline_interfaces.msg import WallDetection


class SonarSweepMap(Node):

    def __init__(self):
        super().__init__('sonar_sweep_map')

        # --- Parametri ---
        self.declare_parameter('intensity_threshold', 200.0)
        self.declare_parameter('peak_proportion', 1.25)
        self.declare_parameter('min_dist_considered', 0.5)
        self.declare_parameter('max_dist_considered', 5.0)
        self.declare_parameter('map_resolution', 0.05)   # m po ćeliji
        self.declare_parameter('map_size_m', 12.0)       # ukupna veličina mape [m]

        self.intensity_threshold = self.get_parameter('intensity_threshold').value
        self.peak_proportion     = self.get_parameter('peak_proportion').value
        self.min_dist            = self.get_parameter('min_dist_considered').value
        self.max_dist            = self.get_parameter('max_dist_considered').value
        self.resolution          = self.get_parameter('map_resolution').value
        self.map_size_m          = self.get_parameter('map_size_m').value

        # Dimenzije grida (kvadrat, robot u sredini)
        self.grid_cells   = int(self.map_size_m / self.resolution)
        self.origin_offset = self.map_size_m / 2.0

        # Matrica mape: -1 = nepoznato, 0 = slobodno, 100 = zauzeto
        self._grid = np.full((self.grid_cells, self.grid_cells), -1, dtype=np.int8)

        # --- Subscriber ---
        self.sub_pc = self.create_subscription(
            PointCloud2,
            '/micron_sonar/point_cloud2',
            self._pc_cb,
            10)

        # --- Publisheri ---
        self.map_pub  = self.create_publisher(OccupancyGrid, '/sonar/occupancy_grid', 1)
        self.wall_pub = self.create_publisher(WallDetection, '/sonar/wall_detection', 10)

        self.get_logger().info(
            f"SonarSweepMap pokrenut — kontinuirani mod (update po pingu)\n"
            f"Rezolucija: {self.resolution*100:.0f} cm/ćelija, "
            f"Mapa: {self.map_size_m:.0f}×{self.map_size_m:.0f} m, "
            f"{self.grid_cells}×{self.grid_cells} ćelija"
        )

    def _pc_cb(self, msg: PointCloud2):
        try:
            pts = point_cloud2.read_points_list(
                msg, field_names=('x', 'y', 'z', 'intensity'), skip_nans=True)
            if not pts:
                return

            pts_arr     = np.array(pts, dtype=np.float64)
            xs          = pts_arr[:, 0]
            ys          = pts_arr[:, 1]
            intensities = pts_arr[:, 3]
            distances   = np.sqrt(xs**2 + ys**2)

            # --- Detekcija refleksije ---
            range_ok     = (distances >= self.min_dist) & (distances <= self.max_dist)
            intensity_ok = range_ok & (intensities >= self.intensity_threshold)
            if not np.any(intensity_ok):
                return

            # Leading edge
            first_peak_idx = None
            for i in range(1, len(intensities)):
                if not intensity_ok[i]:
                    continue
                if intensities[i] >= self.peak_proportion * max(intensities[i - 1], 1.0):
                    first_peak_idx = i
                    break
            if first_peak_idx is None:
                return

            # Centroid pika
            peak_end = first_peak_idx
            for j in range(first_peak_idx + 1, len(intensities)):
                if intensity_ok[j]:
                    peak_end = j
                else:
                    break

            peak_idx = np.arange(first_peak_idx, peak_end + 1)
            peak_int = intensities[peak_idx]
            best     = peak_idx[np.argmax(peak_int)]
            wx       = float(xs[best])
            wy       = float(ys[best])

            # --- Per-beam: objavi WallDetection ---
            wall_msg = WallDetection()
            wall_msg.header.stamp     = msg.header.stamp
            wall_msg.header.frame_id  = msg.header.frame_id
            wall_msg.distance_m       = float(distances[best])
            wall_msg.middle_angle_deg = float(np.degrees(np.arctan2(wy, wx)))
            self.wall_pub.publish(wall_msg)

            # --- Upiši u grid, odmah publishaj ---
            self._trace_ray(wx, wy)
            self._publish_map(msg.header)

        except Exception as e:
            self.get_logger().error(f"_pc_cb greška: {e}\n{traceback.format_exc()}")

    # ------------------------------------------------------------------
    def _world_to_cell(self, x: float, y: float):
        col = int((x + self.origin_offset) / self.resolution)
        row = int((y + self.origin_offset) / self.resolution)
        return row, col

    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.grid_cells and 0 <= col < self.grid_cells

    def _trace_ray(self, wx: float, wy: float):
        """
        Bresenhamov algoritam: od robota (0,0) do odražene točke (wx, wy).
        Sve ćelije na putu → slobodne (0).
        Posljednja ćelija → zauzeto (100).
        """
        r0, c0 = self._world_to_cell(0.0, 0.0)
        r1, c1 = self._world_to_cell(wx, wy)

        if not self._in_bounds(r1, c1):
            return

        cells = _bresenham(c0, r0, c1, r1)

        for c, r in cells[:-1]:
            if self._in_bounds(r, c):
                if self._grid[r, c] != 100:
                    self._grid[r, c] = 0

        cr, cc = cells[-1]
        if self._in_bounds(cr, cc):
            self._grid[cr, cc] = 100

    # ------------------------------------------------------------------
    def _publish_map(self, header):
        og = OccupancyGrid()
        og.header.stamp    = self.get_clock().now().to_msg()
        og.header.frame_id = header.frame_id

        og.info.resolution = self.resolution
        og.info.width      = self.grid_cells
        og.info.height     = self.grid_cells

        og.info.origin.position.x = -self.origin_offset
        og.info.origin.position.y = -self.origin_offset
        og.info.origin.position.z = 0.0
        og.info.origin.orientation.w = 1.0

        og.data = self._grid.flatten().tolist()

        self.map_pub.publish(og)


# ------------------------------------------------------------------
def _bresenham(x0: int, y0: int, x1: int, y1: int):
    cells = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        cells.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return cells


# ------------------------------------------------------------------
def main(args=None):
    rclpy.init(args=args)
    node = SonarSweepMap()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
