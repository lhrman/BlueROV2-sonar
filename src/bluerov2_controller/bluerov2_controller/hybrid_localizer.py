#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32
import math

class HybridLocalizer(Node):
    def __init__(self):
        super().__init__('hybrid_localizer')

        # --- Pool Dimensions (Meters) ---
        self.POOL_LENGTH_X = 25.0 
        self.POOL_WIDTH_Y = 12.5

        # --- Placeholders ---
        self.dist_front = None
        self.dist_left = None
        self.current_yaw_deg = 0.0
        self.latest_tag_msg = None

        # --- Subscribers ---
        self.create_subscription(Float32, '/distance/front', self.front_dist_callback, 10)
        self.create_subscription(Float32, '/distance/left', self.left_dist_callback, 10)
        self.create_subscription(PoseStamped, '/apriltag/pose', self.pose_callback, 10)

        # --- Publisher ---
        self.pub_pose = self.create_publisher(PoseStamped, '/bluerov2/pose', 10)

        self.get_logger().info("Hybrid Localizer Started (Trig Mode). Waiting for data...")

    def front_dist_callback(self, msg):
        self.dist_front = msg.data
        self.compute_and_publish()

    def left_dist_callback(self, msg):
        self.dist_left = msg.data
        self.compute_and_publish()

    def pose_callback(self, msg):
        self.latest_tag_msg = msg
        q = msg.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw_rad = math.atan2(siny_cosp, cosy_cosp)
        self.current_yaw_deg = math.degrees(yaw_rad)
        self.compute_and_publish()

    def compute_and_publish(self):
        if self.dist_front is None or self.dist_left is None or self.latest_tag_msg is None:
            return

        # Normalize yaw to 0-360
        yaw = self.current_yaw_deg % 360
        if yaw < 0: yaw += 360

        calc_x = 0.0
        calc_y = 0.0
        angle_error = 0.0

        # --- TRIGONOMETRIC LOGIC ---
        # 1. Facing EAST (0°) (Range: 315° to 45°)
        if yaw >= 315 or yaw < 45:
            if yaw >= 315: angle_error = yaw - 360
            else:          angle_error = yaw
            
            rad_err = math.radians(angle_error)
            true_front = self.dist_front * math.cos(rad_err)
            true_left  = self.dist_left * math.cos(rad_err)

            calc_x = self.POOL_LENGTH_X - true_front
            calc_y = self.POOL_WIDTH_Y - true_left

        # 2. Facing NORTH (90°) (Range: 45° to 135°)
        elif 45 <= yaw < 135:
            angle_error = yaw - 90
            rad_err = math.radians(angle_error)

            true_front = self.dist_front * math.cos(rad_err)
            true_left  = self.dist_left * math.cos(rad_err)

            calc_x = true_left
            calc_y = self.POOL_WIDTH_Y - true_front

        # 3. Facing WEST (180°) (Range: 135° to 225°)
        elif 135 <= yaw < 225:
            angle_error = yaw - 180
            rad_err = math.radians(angle_error)

            true_front = self.dist_front * math.cos(rad_err)
            true_left  = self.dist_left * math.cos(rad_err)

            calc_x = true_front
            calc_y = true_left

        # 4. Facing SOUTH (270°) (Range: 225° to 315°)
        elif 225 <= yaw < 315:
            angle_error = yaw - 270
            rad_err = math.radians(angle_error)

            true_front = self.dist_front * math.cos(rad_err)
            true_left  = self.dist_left * math.cos(rad_err)

            calc_x = self.POOL_LENGTH_X - true_left
            calc_y = true_front

        # --- Publish Result ---
        out_msg = PoseStamped()
        out_msg.header = self.latest_tag_msg.header
        out_msg.pose.orientation = self.latest_tag_msg.pose.orientation
        out_msg.pose.position.z = self.latest_tag_msg.pose.position.z
        out_msg.pose.position.x = float(calc_x)
        out_msg.pose.position.y = float(calc_y)

        self.pub_pose.publish(out_msg)

        # Logging!
        self.get_logger().info(f"Yaw: {yaw:.0f}° (Err: {angle_error:.0f}°) | RawF: {self.dist_front:.1f}m -> X: {calc_x:.2f} | RawL: {self.dist_left:.1f}m -> Y: {calc_y:.2f}")

def main(args=None):
    rclpy.init(args=args)
    node = HybridLocalizer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()