#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
from tf2_ros import TransformBroadcaster, Buffer, TransformListener

class CameraMapOdom(Node):
    def __init__(self):
        super().__init__('camera_map_odom')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.create_subscription(
            PoseWithCovarianceStamped, '/tag_3/position', self.cb, 10)

    def cb(self, msg):
        try:
            odom_to_base = self.tf_buffer.lookup_transform(
                'odom', 'base_link',
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.1))
        except Exception:
            return

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'map'
        t.child_frame_id = 'odom'
        t.transform.translation.x = msg.pose.pose.position.x - odom_to_base.transform.translation.x
        t.transform.translation.y = msg.pose.pose.position.y - odom_to_base.transform.translation.y
        t.transform.translation.z = 0.0
        t.transform.rotation = msg.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(CameraMapOdom())

if __name__ == '__main__':
    main()
