#!/usr/bin/env python3
"""
Sonar LaserScan Assembler
--------------------------
Skuplja beame Micron sonara (jedan beam/ping) kroz jedan puni krug
i publishuje sensor_msgs/LaserScan na /scan za slam_toolbox.

Svaki beam koji nema detekciju → range_max (slobodan prostor).
Svaki beam koji ima detekciju → izmjerena udaljenost.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, LaserScan
from geometry_msgs.msg import PoseStamped
from sensor_msgs_py import point_cloud2
import numpy as np
import traceback
from scipy.spatial.transform import Rotation


class SonarScanAssembler(Node):

    def __init__(self):
        super().__init__('sonar_scan_assembler')

        # --- Parametri ---
        self.declare_parameter('intensity_threshold', 200.0)
        self.declare_parameter('peak_proportion', 1.25)
        self.declare_parameter('min_range_m', 0.3)
        self.declare_parameter('max_range_m', 5.0)
        self.declare_parameter('min_sweep_deg', 350.0)  # kut za "puni krug"

        self.intensity_threshold = self.get_parameter('intensity_threshold').value
        self.peak_proportion     = self.get_parameter('peak_proportion').value
        self.min_range           = self.get_parameter('min_range_m').value
        self.max_range           = self.get_parameter('max_range_m').value
        self.min_sweep_deg       = self.get_parameter('min_sweep_deg').value

        # --- Stanje ---
        self.current_yaw_deg  = None
        self.prev_yaw_deg     = None
        self._yaw_accumulated = 0.0
        self._beams: list[tuple[float, float]] = []  # (angle_rad, range_m)
        self._sweep_start_stamp = None

        # --- Subscriberi ---
        self.create_subscription(
            PoseStamped,
            '/micron_sonar/heading',
            self._heading_cb,
            10)

        self.create_subscription(
            PointCloud2,
            '/micron_sonar/point_cloud2',
            self._pc_cb,
            10)

        # --- Publisher ---
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)

        self.get_logger().info(
            f"SonarScanAssembler pokrenut\n"
            f"Skuplja beame dok ne napravi {self.min_sweep_deg:.0f}° kruga, "
            f"pa publishuje LaserScan na /scan"
        )

    # ------------------------------------------------------------------
    def _heading_cb(self, msg: PoseStamped):
        q = msg.pose.orientation
        r = Rotation.from_quat([q.x, q.y, q.z, q.w])
        self.current_yaw_deg = float(np.degrees(r.as_euler('xyz')[2]))

    # ------------------------------------------------------------------
    def _pc_cb(self, msg: PointCloud2):
        if self.current_yaw_deg is None:
            return

        current_yaw = self.current_yaw_deg

        # Akumulacija kuta
        if self.prev_yaw_deg is not None:
            delta = current_yaw - self.prev_yaw_deg
            if delta > 180.0:
                delta -= 360.0
            elif delta < -180.0:
                delta += 360.0
            self._yaw_accumulated += abs(delta)
        self.prev_yaw_deg = current_yaw

        if self._sweep_start_stamp is None:
            self._sweep_start_stamp = msg.header.stamp

        # Pokušaj detektirati refleksiju
        detected_range = self._detect_range(msg)

        # Kut beama iz koordinata točke (sonar frame)
        beam_angle_rad = np.radians(current_yaw)

        # Ako nema detekcije → max_range (slobodan prostor)
        r = detected_range if detected_range is not None else self.max_range
        self._beams.append((beam_angle_rad, r))

        # Provjeri je li krug gotov
        if self._yaw_accumulated >= self.min_sweep_deg:
            self._publish_scan(msg.header)
            self._reset_sweep()

    # ------------------------------------------------------------------
    def _detect_range(self, msg: PointCloud2) -> float | None:
        """Vrati udaljenost refleksije ili None ako nema detekcije."""
        try:
            pts = point_cloud2.read_points_list(
                msg, field_names=('x', 'y', 'z', 'intensity'), skip_nans=True)
            if not pts:
                return None

            pts_arr     = np.array(pts, dtype=np.float64)
            xs          = pts_arr[:, 0]
            ys          = pts_arr[:, 1]
            intensities = pts_arr[:, 3]
            distances   = np.sqrt(xs**2 + ys**2)

            range_ok     = (distances >= self.min_range) & (distances <= self.max_range)
            intensity_ok = range_ok & (intensities >= self.intensity_threshold)
            if not np.any(intensity_ok):
                return None

            # Leading edge peak
            for i in range(1, len(intensities)):
                if not intensity_ok[i]:
                    continue
                if intensities[i] >= self.peak_proportion * max(intensities[i - 1], 1.0):
                    peak_end = i
                    for j in range(i + 1, len(intensities)):
                        if intensity_ok[j]:
                            peak_end = j
                        else:
                            break
                    peak_idx = np.arange(i, peak_end + 1)
                    best = peak_idx[np.argmax(intensities[peak_idx])]
                    return float(distances[best])

        except Exception as e:
            self.get_logger().error(f"_detect_range greška: {e}\n{traceback.format_exc()}")

        return None

    # ------------------------------------------------------------------
    def _publish_scan(self, header):
        if not self._beams:
            return

        angles = np.array([b[0] for b in self._beams])
        ranges = np.array([b[1] for b in self._beams])

        # Sortiraj po kutu
        order  = np.argsort(angles)
        angles = angles[order]
        ranges = ranges[order]

        scan = LaserScan()
        scan.header.stamp    = self.get_clock().now().to_msg()
        scan.header.frame_id = header.frame_id

        scan.angle_min       = float(angles[0])
        scan.angle_max       = float(angles[-1])
        scan.angle_increment = float(np.mean(np.diff(angles))) if len(angles) > 1 else 0.0
        scan.time_increment  = 0.0
        scan.scan_time       = float(
            (rclpy.time.Time.from_msg(header.stamp) -
             rclpy.time.Time.from_msg(self._sweep_start_stamp)).nanoseconds * 1e-9
        ) if self._sweep_start_stamp else 0.0
        scan.range_min       = self.min_range
        scan.range_max       = self.max_range
        scan.ranges          = ranges.tolist()

        self.scan_pub.publish(scan)
        self.get_logger().info(
            f"LaserScan objavljen: {len(ranges)} beama, "
            f"{np.degrees(scan.angle_min):.1f}° → {np.degrees(scan.angle_max):.1f}°"
        )

    # ------------------------------------------------------------------
    def _reset_sweep(self):
        self._beams.clear()
        self._yaw_accumulated  = 0.0
        self._sweep_start_stamp = None


# ------------------------------------------------------------------
def main(args=None):
    rclpy.init(args=args)
    node = SonarScanAssembler()
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
