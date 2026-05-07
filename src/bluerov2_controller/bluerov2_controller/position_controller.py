#!/usr/bin/env python3
# --- FINAL VERSION: AprilTag Yaw + Physical Lever Arm Correction ---
import rclpy
import json
import math
from rclpy.node import Node

from geometry_msgs.msg import PoseWithCovarianceStamped, Point
from std_msgs.msg import UInt16, String, Bool

# --- PHYSICAL OFFSETS (Lever Arm) ---
# Distance from ROV Center -> AprilTag Center (in Meters)
# You said the tag is "Back Right".
TAG_OFFSET_X = -0.035  # -3.5 cm (Negative = Back)
TAG_OFFSET_Y = -0.05   # -5.0 cm (Negative = Right)
# ------------------------------------

class PositionController(Node):

    def __init__(self):
        super().__init__("position_controller")

        # --- Parameters ---
        self.declare_parameter("kp_x", 0.0); self.declare_parameter("ki_x", 0.0); self.declare_parameter("kd_x", 0.0)
        self.declare_parameter("kp_y", 0.0); self.declare_parameter("ki_y", 0.0); self.declare_parameter("kd_y", 0.0)
        self.declare_parameter("pwm_neutral", 1500.0)
        self.declare_parameter("move_pwm_range", 200.0) 
        self.declare_parameter("enable", False)

        self.kp_x = self.get_parameter("kp_x").value; self.ki_x = self.get_parameter("ki_x").value; self.kd_x = self.get_parameter("kd_x").value
        self.kp_y = self.get_parameter("kp_y").value; self.ki_y = self.get_parameter("ki_y").value; self.kd_y = self.get_parameter("kd_y").value
        self.pwm_neutral = self.get_parameter("pwm_neutral").value
        self.move_pwm_range = self.get_parameter("move_pwm_range").value
        self.pwm_max = self.pwm_neutral + self.move_pwm_range
        self.pwm_min = self.pwm_neutral - self.move_pwm_range
        self.enable = self.get_parameter("enable").value

        # --- State Variables ---
        self.tag_x = 0.0; self.tag_y = 0.0    # Raw position of the tag/camera
        self.current_x = 0.0; self.current_y = 0.0 # Calculated position of ROV CENTER
        self.current_yaw = 0.0 # Radians (from AprilTag)
        
        self.target_x = 0.0; self.target_y = 0.0
        self.integral_x = 0.0; self.prev_error_x = 0.0
        self.integral_y = 0.0; self.prev_error_y = 0.0
        self.last_time = None 
        self.has_pose = False

        # --- Subscribers ---
        self.pose_sub = self.create_subscription(PoseWithCovarianceStamped, "/tag_3/position", self.pose_callback, 10)
        self.target_sub = self.create_subscription(Point, "/target_position", self.target_callback, 10)
        self.enable_sub = self.create_subscription(Bool, "/settings/position/set_enable", self.enable_callback, 10)

        # --- Publishers ---
        self.forward_pub = self.create_publisher(UInt16, "/bluerov2/rc/forward", 10)
        self.lateral_pub = self.create_publisher(UInt16, "/bluerov2/rc/lateral", 10)
        self.status_pub = self.create_publisher(String, '/settings/position/status', 10) 

        # --- Timers ---
        self.control_timer = self.create_timer(0.05, self.control_loop)
        self.debug_timer = self.create_timer(1.0, self.publish_debug_log)
        self.debug_output = {} 

        self.get_logger().info(f"Position Controller Started. Lever Arm: X={TAG_OFFSET_X}, Y={TAG_OFFSET_Y}")

    def pose_callback(self, msg):
        # 1. Store Raw Tag Position
        self.tag_x = msg.pose.pose.position.x
        self.tag_y = msg.pose.pose.position.y
        
        # 2. Get Yaw from AprilTag (Quaternion -> Euler)
        q = msg.pose.pose.orientation
        t3 = +2.0 * (q.w * q.z + q.x * q.y)
        t4 = +1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(t3, t4)
        
        self.has_pose = True 

    def update_rov_center(self):
        """
        Calculates where the ROV CENTER is, based on where the TAG is.
        Formula: P_rov = P_tag - Rotated_Offset
        """
        # Calculate rotation components based on CURRENT YAW
        cos_yaw = math.cos(self.current_yaw)
        sin_yaw = math.sin(self.current_yaw)
        
        # Rotate the offset vector (Standard 2D Rotation)
        offset_x_rotated = (TAG_OFFSET_X * cos_yaw) - (TAG_OFFSET_Y * sin_yaw)
        offset_y_rotated = (TAG_OFFSET_X * sin_yaw) + (TAG_OFFSET_Y * cos_yaw)
        
        # Apply to find true center
        self.current_x = self.tag_x - offset_x_rotated
        self.current_y = self.tag_y - offset_y_rotated

    def target_callback(self, msg):
        self.target_x = msg.x
        self.target_y = msg.y
        self.get_logger().info(f"New target: X={self.target_x}, Y={self.target_y}")
        self.integral_x = 0.0; self.integral_y = 0.0

    def enable_callback(self, msg):
        if not self.enable and msg.data: # Just turning ON
            self.get_logger().info("Position Hold ENABLED")
            if self.has_pose:
                # Calculate true center before locking target
                self.update_rov_center()
                self.target_x = self.current_x
                self.target_y = self.current_y
                self.get_logger().info(f"Target locked at ROV CENTER: X={self.target_x:.2f}, Y={self.target_y:.2f}")
            else:
                self.target_x = 0.0; self.target_y = 0.0
            
            self.integral_x = 0.0; self.prev_error_x = 0.0
            self.integral_y = 0.0; self.prev_error_y = 0.0
            self.last_time = None
        elif self.enable and not msg.data:
            self.get_logger().info("Position Hold DISABLED")
            neutral_msg = UInt16(); neutral_msg.data = int(self.pwm_neutral)
            self.forward_pub.publish(neutral_msg); self.lateral_pub.publish(neutral_msg)
            
        self.enable = msg.data
        self.publish_status() 

    def control_loop(self):
        self.publish_status() 

        if not self.enable:
            self.integral_x = 0.0; self.prev_error_x = 0.0
            self.integral_y = 0.0; self.prev_error_y = 0.0
            self.last_time = None
            return 

        if not self.has_pose:
            self.get_logger().warn("Waiting for AprilTag pose...")
            return

        current_time = self.get_clock().now()
        if self.last_time is None: dt = 0.05
        else: dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time
        if dt <= 0: return 

        # --- 1. CALCULATE ROV CENTER ---
        self.update_rov_center()

        # --- 2. CALCULATE ERROR (Based on Center) ---
        error_x = self.target_x - self.current_x
        error_y = self.target_y - self.current_y

        # --- 3. PID (Pool Frame) ---
        self.integral_x += error_x * dt
        derivative_x = (error_x - self.prev_error_x) / dt
        thrust_pool_x = (self.kp_x * error_x) + (self.ki_x * self.integral_x) + (self.kd_x * derivative_x)
        self.prev_error_x = error_x

        self.integral_y += error_y * dt
        derivative_y = (error_y - self.prev_error_y) / dt
        thrust_pool_y = (self.kp_y * error_y) + (self.ki_y * self.integral_y) + (self.kd_y * derivative_y)
        self.prev_error_y = error_y
        
        # --- 4. CLAMP THRUST (Constant Speed) ---
        max_thrust = self.move_pwm_range 
        thrust_pool_x = max(-max_thrust, min(max_thrust, thrust_pool_x))
        thrust_pool_y = max(-max_thrust, min(max_thrust, thrust_pool_y))

        # --- 5. ROTATE THRUST TO ROV FRAME ---
        # We use the AprilTag Yaw for this rotation
        yaw = self.current_yaw
        cos_yaw = math.cos(yaw); sin_yaw = math.sin(yaw)
        
        # Based on your test (X=Left, Y=Forward)
        thrust_forward = thrust_pool_y * cos_yaw + thrust_pool_x * sin_yaw
        thrust_lateral = -thrust_pool_y * sin_yaw + thrust_pool_x * cos_yaw
        
        # --- 6. OUTPUT PWM ---
        pwm_forward = self.pwm_neutral + thrust_forward
        pwm_lateral = self.pwm_neutral + thrust_lateral

        pwm_forward_sat = max(self.pwm_min, min(self.pwm_max, pwm_forward))
        pwm_lateral_sat = max(self.pwm_min, min(self.pwm_max, pwm_lateral))
        
        # Debug Output
        self.debug_output = {
            "TGT": (self.target_x, self.target_y), 
            "ROV": (self.current_x, self.current_y), # Calculated Center
            "TAG": (self.tag_x, self.tag_y),         # Raw Tag
            "YAW": math.degrees(yaw),
            "PWM": (int(pwm_forward_sat), int(pwm_lateral_sat))
        }

        forward_msg = UInt16(); forward_msg.data = int(pwm_forward_sat)
        lateral_msg = UInt16(); lateral_msg.data = int(pwm_lateral_sat)
        self.forward_pub.publish(forward_msg)
        self.lateral_pub.publish(lateral_msg)

    def publish_debug_log(self):
        if self.enable and self.debug_output:
            self.get_logger().info(
                f"TGT:({self.debug_output['TGT'][0]:.2f},{self.debug_output['TGT'][1]:.2f}) "
                f"ROV:({self.debug_output['ROV'][0]:.2f},{self.debug_output['ROV'][1]:.2f}) "
                f"TAG:({self.debug_output['TAG'][0]:.2f},{self.debug_output['TAG'][1]:.2f}) "
                f"YAW:{self.debug_output['YAW']:.1f} "
                f"PWM:({self.debug_output['PWM'][0]},{self.debug_output['PWM'][1]})"
            )

    def publish_status(self):
        msg = String()
        data = { "type": "position_controller", "enable": self.enable,
            "target_x": self.target_x, "target_y": self.target_y,
            "current_x": round(self.current_x, 2), "current_y": round(self.current_y, 2),
            "current_yaw": round(math.degrees(self.current_yaw), 1)
        }
        msg.data = json.dumps(data)
        self.status_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = PositionController()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        neutral_msg = UInt16(); neutral_msg.data = int(node.pwm_neutral)
        node.forward_pub.publish(neutral_msg); node.lateral_pub.publish(neutral_msg)
        node.get_logger().info("Position controller shutting down.")
        node.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()