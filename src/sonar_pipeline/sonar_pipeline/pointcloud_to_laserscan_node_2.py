#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud, LaserScan
import numpy as np
import math

class PointCloudToLaserScan(Node):
    def __init__(self):
        super().__init__('pointcloud_to_laserscan')
        self.declare_parameter('min_height', -0.5)
        self.declare_parameter('max_height',  0.5)
        self.declare_parameter('angle_increment', math.radians(1.0))
        self.declare_parameter('min_range', 1.0)
        self.declare_parameter('max_range', 6.0)
        self.declare_parameter('publish_on_every_update', True)

        self.min_height = self.get_parameter('min_height').value
        self.max_height = self.get_parameter('max_height').value
        self.angle_increment = self.get_parameter('angle_increment').value
        self.min_range = self.get_parameter('min_range').value
        self.max_range = self.get_parameter('max_range').value
        self.publish_on_every_update = self.get_parameter('publish_on_every_update').value

        self.angle_min = -math.pi
        self.angle_max  = math.pi
        self.num_beams = 359  # eksplicitno

        self.accumulated_ranges = np.full(self.num_beams, np.inf)
        self.last_header = None

        # --- Ping-pong tracking ---
        self.last_beam_angle = None      # kut zadnjeg POJEDINAČNOG zraka
        self.scan_direction = None       # +1 = raste, -1 = pada
        self.reversal_count = 0          # broj obrata

        self.sub = self.create_subscription(
            PointCloud,
            '/micron_sonar/point_cloud',
            self.pc_callback,
            10)
        self.pub = self.create_publisher(LaserScan, '/scan', 10)

        self.timer = self.create_timer(0.1, self.publish_scan)

        self.get_logger().info(f"Sonar Converter pokrenut. Rezolucija: {self.num_beams} zraka.")

    def pc_callback(self, msg: PointCloud):
        if not msg.points:
            return

        self.last_header = msg.header

        xs = np.array([p.x for p in msg.points])
        ys = np.array([p.y for p in msg.points])
        zs = np.array([p.z for p in msg.points])

        distances_all = np.sqrt(xs**2 + ys**2)
        mask = (
            (zs >= self.min_height) & (zs <= self.max_height) &
            (distances_all >= self.min_range) & (distances_all <= self.max_range)
        )

        valid_xs = xs[mask]
        valid_ys = ys[mask]
        distances = distances_all[mask]

        # Upiši u buffer čak i ako nema valjanih točaka u ovom zraku
        # (da ne propustimo detekciju kuta)
        angles_all = np.arctan2(ys, xs)
        current_beam_angle = float(np.median(angles_all))  # reprezentativni kut ovog zraka

        # --- Detekcija smjera i obrata (ping-pong) ---
        if self.last_beam_angle is not None:
            delta = current_beam_angle - self.last_beam_angle

            # Zanemari skok manji od pola koraka (šum)
            if abs(delta) > self.angle_increment * 0.5:
                new_direction = 1 if delta > 0 else -1

                if self.scan_direction is not None and new_direction != self.scan_direction:
                    # *** OBRAT SMJERA = jedna puna "rotacija" ***
                    self.reversal_count += 1
                    valid_count = int(np.sum(np.isfinite(self.accumulated_ranges)))
                    self.get_logger().info(
                        f"Obrat #{self.reversal_count}! Smjer: "
                        f"{'→ (+)' if new_direction > 0 else '← (-)'} | "
                        f"Kut obrata: {math.degrees(current_beam_angle):.1f}° | "
                        f"Valjanih zraka: {valid_count}/{self.num_beams}"
                    )
                    self.publish_scan()
                    # Reset akumulatora za novi sweep
                    self.accumulated_ranges = np.full(self.num_beams, np.inf)

                self.scan_direction = new_direction

        self.last_beam_angle = current_beam_angle

        # Upiši valjane točke u buffer
        if distances.size > 0:
            angles_valid = np.arctan2(valid_ys, valid_xs)
            beam_indices = ((angles_valid - self.angle_min) / self.angle_increment).astype(int)
            beam_indices = np.clip(beam_indices, 0, self.num_beams - 1)

            for i in range(len(distances)):
                idx = beam_indices[i]
                if distances[i] < self.accumulated_ranges[idx]:
                    self.accumulated_ranges[idx] = float(distances[i])

        if self.publish_on_every_update:
            self.publish_scan()

    def publish_scan(self):
        if self.last_header is None:
            return

        scan = LaserScan()
        scan.header = self.last_header
        scan.header.frame_id = 'sonar_frame'
        scan.angle_min = self.angle_min
        scan.angle_max = self.angle_max
        scan.angle_increment = self.angle_increment
        scan.time_increment = 0.0
        scan.scan_time = 0.1
        scan.range_min = self.min_range
        scan.range_max = self.max_range
        scan.ranges = self.accumulated_ranges.tolist()
        scan.intensities = []

        self.pub.publish(scan)

def main(args=None):
    rclpy.init(args=args)
    node = PointCloudToLaserScan()
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