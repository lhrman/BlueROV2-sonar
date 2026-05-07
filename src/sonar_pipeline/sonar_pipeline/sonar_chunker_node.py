#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from sensor_msgs.msg import PointCloud2, PointField
from geometry_msgs.msg import PoseStamped
from sensor_msgs_py import point_cloud2
import tf2_ros
import tf2_sensor_msgs
from tf2_ros import TransformException
import numpy as np
from scipy.spatial.transform import Rotation
import traceback

from sonar_pipeline_interfaces.msg import WallDetection

class ChunkingWallDetector(Node):
    def __init__(self):
        super().__init__('chunking_wall_detector')

        # --- Parameters ---
        self.declare_parameter('fixed_frame', 'sonar_frame')
        self.declare_parameter('intensity_threshold', 100.0)
        # Hysteresis: We must move this many degrees in the NEW direction 
        # before we confirm the sweep has ended.
        self.declare_parameter('turn_threshold_deg', 1.0) 
        
        self.fixed_frame = self.get_parameter('fixed_frame').value
        self.intensity_threshold = self.get_parameter('intensity_threshold').value
        self.turn_threshold_rad = np.deg2rad(self.get_parameter('turn_threshold_deg').value)

        # --- TF2 Setup ---
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # --- Publishers ---
        self.chunk_pub = self.create_publisher(PointCloud2, '/micron_sonar/chunked_cloud', 10)
        self.wall_pub = self.create_publisher(WallDetection, '/wall_detection', 10)

        # --- Subscribers ---
        self.subscription_pc = self.create_subscription(
            PointCloud2,
            '/micron_sonar/point_cloud2', 
            self.pc_callback,
            10)
        
        self.subscription_heading = self.create_subscription(
            PoseStamped,
            '/micron_sonar/heading',
            self.heading_callback,
            10)

        # --- State Machine Buffers ---
        self.main_buffer = []          # Points confirmed to be in the current sweep
        self.candidate_buffer = []     # Points that might be part of a turn (waiting to see)
        
        self.current_yaw_rad = None
        self.last_header = None
        
        # State tracking
        # Direction: 1 = Increasing (Counter-Clockwise), -1 = Decreasing (Clockwise), 0 = Init
        self.sweep_direction = 0 
        self.extreme_yaw_rad = None    # The furthest angle reached in the current direction

        self.output_fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name='intensity', offset=12, datatype=PointField.FLOAT32, count=1),
        ]

        self.get_logger().info("Robust Sweep Detector started.")
        self.get_logger().info(f"Turn Threshold (Hysteresis): {self.get_parameter('turn_threshold_deg').value} deg")

    def heading_callback(self, msg: PoseStamped):
        try:
            q = msg.pose.orientation
            r = Rotation.from_quat([q.x, q.y, q.z, q.w])
            rpy = r.as_euler('xyz') 
            self.current_yaw_rad = rpy[2]
        except Exception as e:
            self.get_logger().error(f"Error in heading callback: {e}")

    def pc_callback(self, msg: PointCloud2):
        try:
            current_yaw = self.current_yaw_rad
            if current_yaw is None:
                return

            # --- 1. Transform Points ---
            if self.fixed_frame == msg.header.frame_id:
                cloud_in_fixed = msg
            else:
                trans_fixed = self.tf_buffer.lookup_transform(
                    self.fixed_frame,
                    msg.header.frame_id,
                    msg.header.stamp,
                    timeout=Duration(seconds=0.1))
                cloud_in_fixed = tf2_sensor_msgs.do_transform_cloud(msg, trans_fixed)

            new_points = point_cloud2.read_points_list(
                cloud_in_fixed, field_names=('x', 'y', 'z', 'intensity'), skip_nans=True
            )
            if not new_points:
                return

            self.last_header = msg.header

            # --- 2. Initialize State if needed ---
            if self.extreme_yaw_rad is None:
                self.extreme_yaw_rad = current_yaw
                self.main_buffer.extend(new_points)
                return

            # --- 3. Robust Direction Logic ---
            
            # Determine "instant" movement relative to the furthest point reached
            delta_from_extreme = current_yaw - self.extreme_yaw_rad
            
            # Check if we are continuing the current trend or reversing
            is_continuing_trend = False
            
            if self.sweep_direction == 0:
                # Initialization phase: determine initial direction
                if abs(delta_from_extreme) > 0.001: # Small noise gate
                    self.sweep_direction = 1 if delta_from_extreme > 0 else -1
                    is_continuing_trend = True
            else:
                # Normal operation
                if self.sweep_direction == 1: # Moving Up
                    if delta_from_extreme >= -1e-4: # Allowing tiny jitter
                        is_continuing_trend = True
                else: # Moving Down
                    if delta_from_extreme <= 1e-4:
                        is_continuing_trend = True

            # --- 4. Buffer Management ---
            
            if is_continuing_trend:
                # We are definitely still in the same sweep.
                # 1. If we had a "candidate buffer" (thought we were turning), 
                #    it was just noise. Merge it back into main.
                if self.candidate_buffer:
                    self.main_buffer.extend(self.candidate_buffer)
                    self.candidate_buffer = []
                
                # 2. Add new points
                self.main_buffer.extend(new_points)
                
                # 3. Update the "Furthest" point reached
                self.extreme_yaw_rad = current_yaw
                
            else:
                # We are moving in the OPPOSITE direction.
                # This could be a real turn, or just jitter.
                self.candidate_buffer.extend(new_points)
                
                # CHECK: Have we moved enough to confirm a turn?
                # We compare current yaw to the extreme yaw we recorded.
                dist_from_extreme = abs(delta_from_extreme)
                
                if dist_from_extreme > self.turn_threshold_rad:
                    # !!! TURN CONFIRMED !!!
                    
                    # 1. Process the COMPLETED sweep (main_buffer)
                    # Use the extreme angle as the end of the previous sweep
                    self.process_and_publish(self.main_buffer)
                    
                    # 2. Reset for the NEW sweep
                    # The 'candidate_buffer' actually belongs to the new sweep
                    self.main_buffer = self.candidate_buffer
                    self.candidate_buffer = []
                    
                    # 3. Flip direction and update state
                    self.sweep_direction = -1 * self.sweep_direction
                    self.extreme_yaw_rad = current_yaw # The new sweep starts here
                    
                    # Log for debugging
                    self.get_logger().info(f"Turn confirmed. New Direction: {self.sweep_direction}")

        except TransformException as e:
            self.get_logger().warn(f"TF Error: {e}")
        except Exception as e:
            self.get_logger().error(f"Callback Error: {e}\n{traceback.format_exc()}")
            # Reset on critical error
            self.main_buffer = []
            self.candidate_buffer = []
            self.extreme_yaw_rad = None

    def process_and_publish(self, points_list):
        if not points_list or self.last_header is None:
            return

        # --- 1) Visualization (Keep this to see what's happening) ---
        chunk_header = self.last_header
        chunk_header.stamp = self.get_clock().now().to_msg()
        chunk_header.frame_id = self.fixed_frame

        try:
            chunk_msg = point_cloud2.create_cloud(chunk_header, self.output_fields, points_list)
            self.chunk_pub.publish(chunk_msg)
        except Exception:
            pass

        # --- 2) Convert to Numpy ---
        points_array = np.array(points_list, dtype=np.float64)
        intens = points_array[:, 3]

        strong_mask = intens >= self.intensity_threshold
        strong_points = points_array[strong_mask]

        if strong_points.shape[0] == 0:
            return  # No points strong enough, abandon

        # --- 4) Distance Calculation (Closest Point) ---
        # Calculate distance to all strong points
        dists = np.sqrt(strong_points[:, 0]**2 + strong_points[:, 1] **2)

        distance = float(np.min(dists)) + 0.1

        # --- 5) Angle Calculation ---
        # (Kept original logic to find the "center" of the wall, 
        # but you could switch this to the angle of the closest point if preferred)
        angle_src = strong_points
        angles = np.arctan2(angle_src[:, 1], angle_src[:, 0])
        mean_vector = np.mean(np.exp(1j * angles))
        middle_angle_rad = np.angle(mean_vector)

        # --- 6) Publish ---
        out = WallDetection()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self.fixed_frame
        out.middle_angle_deg = float(np.rad2deg(middle_angle_rad))
        out.distance_m = float(distance)
        self.wall_pub.publish(out)

def main(args=None):
    rclpy.init(args=args)
    node = ChunkingWallDetector()
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