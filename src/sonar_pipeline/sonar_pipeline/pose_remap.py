#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped

class PoseRemap(Node):
    def __init__(self):
        super().__init__('pose_remap')
        self.pub = self.create_publisher(
            PoseWithCovarianceStamped, '/tag_3/position_odom', 10)
        self.create_subscription(
            PoseWithCovarianceStamped, '/tag_3/position', self.cb, 10)

    def cb(self, msg):
        msg.header.frame_id = 'odom'
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = PoseRemap()
    rclpy.spin(node)

if __name__ == '__main__':
    main()