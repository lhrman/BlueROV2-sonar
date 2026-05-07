#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud, LaserScan
import numpy as np
import math
import time
from std_msgs.msg import UInt16
from geometry_msgs.msg import PoseWithCovarianceStamped

class PointCloudToLaserScan(Node):
    def __init__(self):
        super().__init__('pointcloud_to_laserscan')
        self.declare_parameter('min_height', -0.5)
        self.declare_parameter('max_height',  0.5)
        self.declare_parameter('angle_increment', math.radians(1.0))
        self.declare_parameter('min_range', 1.0)
        self.declare_parameter('max_range', 6.0)
        self.declare_parameter('publish_on_every_update', False)

        self.pwm_forward = 1500
        self.pwm_lateral = 1500
        self.pwm_yaw = 1500
        self.pwm_neutral = 1500
        self.pwm_threshold = 25
        self.pwm_timeout = 0.5
        self.pwm_yaw_threshold = 50
        self.last_forward_time = time.time() - self.pwm_timeout - 1.0
        self.last_lateral_time = time.time() - self.pwm_timeout - 1.0

        self.is_stopped = True
        self.cooldown_after_scan = 5.0
        self.scan_published_time = None
        self.waiting_for_cooldown = False
        self.latest_camera_pose = None

        self.min_height = self.get_parameter('min_height').value
        self.max_height = self.get_parameter('max_height').value
        self.angle_increment = self.get_parameter('angle_increment').value
        self.min_range = self.get_parameter('min_range').value
        self.max_range = self.get_parameter('max_range').value
        self.publish_on_every_update = self.get_parameter('publish_on_every_update').value

        self.angle_min = -math.pi
        self.angle_increment = 2 * math.pi / 359
        self.angle_max = math.pi - (2 * math.pi / 359)
        self.num_beams = 359

        self.accumulated_ranges = np.full(self.num_beams, np.inf)
        self.last_header = None

        self.last_beam_angle = None
        self.scan_direction = None
        self.reversal_count = 0

        self.sub = self.create_subscription(
            PointCloud, '/micron_sonar/point_cloud', self.pc_callback, 10)
        self.pub = self.create_publisher(LaserScan, '/scan', 10)
        #self.initialpose_pub = self.create_publisher(
        #    PoseWithCovarianceStamped, '/initialpose', 10)

        self.create_subscription(UInt16, '/bluerov2/rc/forward', self.forward_cb, 10)
        self.create_subscription(UInt16, '/bluerov2/rc/lateral', self.lateral_cb, 10)
        self.create_subscription(UInt16, '/bluerov2/rc/yaw', self.yaw_cb, 10)
        self.create_subscription(
            PoseWithCovarianceStamped, '/tag_3/position', self.camera_cb, 10)

        self.create_timer(0.2, self._update_stopped)
        self.get_logger().info(f"Sonar Converter pokrenut. Rezolucija: {self.num_beams} zraka.")

    def camera_cb(self, msg):
        self.latest_camera_pose = msg

    def _reset_buffer(self):
        self.accumulated_ranges = np.full(self.num_beams, np.inf)
        self.last_beam_angle = None
        self.scan_direction = None
        self.reversal_count = 0
        self.waiting_for_cooldown = False
        self.scan_published_time = None

    def _update_stopped(self):
        now = time.time()
        forward_timed_out = (now - self.last_forward_time) > self.pwm_timeout
        lateral_timed_out = (now - self.last_lateral_time) > self.pwm_timeout

        was_stopped = self.is_stopped
        self.is_stopped = (
            (forward_timed_out or abs(self.pwm_forward - self.pwm_neutral) < self.pwm_threshold) and
            (lateral_timed_out or abs(self.pwm_lateral - self.pwm_neutral) < self.pwm_threshold) and
            abs(self.pwm_yaw - self.pwm_neutral) < self.pwm_yaw_threshold
        )

        if was_stopped and not self.is_stopped:
            self._reset_buffer()
            self.get_logger().info('ROV krenuo, resetiram buffer.')

    def forward_cb(self, msg):
        self.pwm_forward = msg.data
        self.last_forward_time = time.time()
        self._update_stopped()

    def lateral_cb(self, msg):
        self.pwm_lateral = msg.data
        self.last_lateral_time = time.time()
        self._update_stopped()

    def yaw_cb(self, msg):
        self.pwm_yaw = msg.data
        self._update_stopped()

    def pc_callback(self, msg: PointCloud):
        if not self.is_stopped:
            return

        if self.waiting_for_cooldown:
            now = self.get_clock().now().nanoseconds / 1e9
            elapsed = now - self.scan_published_time
            if elapsed < self.cooldown_after_scan:
                return
            else:
                self.get_logger().info('Cooldown završen, počinjem novi scan.')
                self._reset_buffer()

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

        distances = distances_all[mask]
        valid_xs = xs[mask]
        valid_ys = ys[mask]

        angles_all = np.arctan2(ys, xs)
        current_beam_angle = float(np.median(angles_all))

        if self.last_beam_angle is not None:
            delta = current_beam_angle - self.last_beam_angle

            if abs(delta) > self.angle_increment * 0.5:
                new_direction = 1 if delta > 0 else -1

                if self.scan_direction is not None and new_direction != self.scan_direction:
                    self.reversal_count += 1
                    self.get_logger().info(
                        f"Obrat #{self.reversal_count} na {math.degrees(current_beam_angle):.1f}° "
                        f"| Smjer: {'→ (+)' if new_direction > 0 else '← (-)'}"
                    )

                    if self.reversal_count >= 2:
                        valid_count = int(np.sum(np.isfinite(self.accumulated_ranges)))
                        self.get_logger().info(
                            f"Puni ping-pong završen! Publishujem scan s "
                            f"{valid_count}/{self.num_beams} valjanih zraka."
                        )
                        self.publish_scan()
                        self._reset_buffer()

                self.scan_direction = new_direction

        self.last_beam_angle = current_beam_angle

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

        if self.latest_camera_pose is not None:
            ip = PoseWithCovarianceStamped()
            ip.header.frame_id = 'map'
            ip.header.stamp = self.get_clock().now().to_msg()
            ip.pose.pose = self.latest_camera_pose.pose.pose
            ip.pose.covariance[0] = 0.25
            ip.pose.covariance[7] = 0.25
            ip.pose.covariance[35] = 0.1
            #self.initialpose_pub.publish(ip)            
            #self.get_logger().info('Initialpose publishan.')
        else:
            pass
            #self.get_logger().warn('Nema camera pose, initialpose nije publishan!')

        scan = LaserScan()
        scan.header = self.last_header
        scan.header.frame_id = 'sonar_frame'
        scan.header.stamp = self.get_clock().now().to_msg()
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

        self.scan_published_time = self.get_clock().now().nanoseconds / 1e9
        self.waiting_for_cooldown = True
        self.get_logger().info(f'Scan publishan. Čekam {self.cooldown_after_scan}s cooldown.')


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