#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
import numpy as np
import traceback

from sonar_pipeline_interfaces.msg import WallDetection


class SonarContinuousMap(Node):
    def __init__(self):
        super().__init__('sonar_continuous_map')

        # --- Parameters ---
        self.declare_parameter('intensity_threshold', 50.0)
        self.declare_parameter('peak_proportion', 1.25)
        self.declare_parameter('min_dist_considered', 0.5)
        self.declare_parameter('max_dist_considered', 5.0)

        self.intensity_threshold = self.get_parameter('intensity_threshold').value
        self.peak_proportion = self.get_parameter('peak_proportion').value
        self.min_dist = self.get_parameter('min_dist_considered').value
        self.max_dist = self.get_parameter('max_dist_considered').value

        # --- Subscriber ---
        self.sub = self.create_subscription(
            PointCloud2,
            '/micron_sonar/point_cloud2',
            self.pc_callback,
            10)

        # --- Publisher ---
        self.wall_pub = self.create_publisher(WallDetection, '/sonar/wall_detection', 10)

        self.get_logger().info("SonarContinuousMap pokrenut — objavljuje udaljenost od zida po beamu.")

    # ------------------------------------------------------------------
    def pc_callback(self, msg: PointCloud2):
        try:
            # --- 1. Sve točke unutar sonar_frame ---
            pts = point_cloud2.read_points_list(
                msg, field_names=('x', 'y', 'z', 'intensity'), skip_nans=True)
            if not pts:
                return

            pts_arr = np.array(pts, dtype=np.float64)
            xs, ys, zs, intensities = pts_arr[:, 0], pts_arr[:, 1], pts_arr[:, 2], pts_arr[:, 3]
            distances = np.sqrt(xs ** 2 + ys ** 2)

            # --- 2. Detekcija zida ---
            # Filtriraj po rasponu udaljenosti i pragu intenziteta
            range_approved = (distances >= self.min_dist) & (distances <= self.max_dist)
            intensity_approved = range_approved & (intensities >= self.intensity_threshold)
            if not np.any(intensity_approved):
                return

            # Nađi leading edge: prvi bin koji naglo raste iznad praga
            first_peak_idx = None
            for i in range(1, len(intensities)):
                if not intensity_approved[i]:
                    continue
                if intensities[i] >= self.peak_proportion * max(intensities[i - 1], 1.0):
                    first_peak_idx = i
                    break

            if first_peak_idx is None:
                return

            # ----------------------------------------------------------------
            # OPTION A — CENTROID (active)
            # Sakupi sve binove koji pripadaju ovom piku (uzastopni strong region)
            peak_end = first_peak_idx
            for j in range(first_peak_idx + 1, len(intensities)):
                if intensity_approved[j]:
                    peak_end = j
                else:
                    break

            peak_indices = np.arange(first_peak_idx, peak_end + 1)
            peak_intensities = intensities[peak_indices]
            peak_distances = distances[peak_indices]

            # Udaljenost = težinska sredina po intenzitetu
            distance = float(np.average(peak_distances, weights=peak_intensities))
            # Smjer od bina s najvišim intenzitetom unutar pika
            best_in_peak = peak_indices[np.argmax(peak_intensities)]
            x_s = float(xs[best_in_peak])
            y_s = float(ys[best_in_peak])

            # ----------------------------------------------------------------
            # OPTION B — LEADING EDGE (zakomentirano)
            # Uzima samo prvi pik bin — konzervativno, bliže zidu
            # x_s = float(xs[first_peak_idx])
            # y_s = float(ys[first_peak_idx])
            # distance = float(distances[first_peak_idx])
            # ----------------------------------------------------------------

            # --- 3. Kut beama u sonar_frame ---
            bearing_deg = float(np.degrees(np.arctan2(y_s, x_s)))

            out = WallDetection()
            out.header.stamp = msg.header.stamp
            out.header.frame_id = msg.header.frame_id  # sonar_frame
            out.distance_m = distance
            out.middle_angle_deg = bearing_deg
            self.wall_pub.publish(out)

            self.get_logger().info(
                f"Zid: {distance:.3f}m @ {bearing_deg:.1f}°"
            )

        except Exception as e:
            self.get_logger().error(f"pc_callback greška: {e}\n{traceback.format_exc()}")


def main(args=None):
    rclpy.init(args=args)
    node = SonarContinuousMap()
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
