#!/usr/bin/env python3
"""
pose_to_tf.py

Prima /tag_3/position (PoseWithCovarianceStamped u map frameu)
i publishe:
  - map → odom (identitet, dinamički da slam_toolbox može pregaziti)
  - odom → base_link (pozicija iz kamere)
  - Slam_toolbox korigira map→odom kad pronađe bolji match
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
import tf2_ros


class PoseToTf(Node):
    def __init__(self):
        super().__init__('pose_to_tf')
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.last_transform = None  # ← novo

        self.create_subscription(
            PoseWithCovarianceStamped,
            '/tag_3/position',
            self.pose_callback,
            10
        )

        # Republisha zadnji TF svake 0.1s
        self.create_timer(0.1, self._republish_tf)

        self.get_logger().info('PoseToTf pokrenut.')

    def _republish_tf(self):
        if self.last_transform is None:
            return
        self.last_transform.header.stamp = self.get_clock().now().to_msg()
        self.tf_broadcaster.sendTransform(self.last_transform)

    def pose_callback(self, msg: PoseWithCovarianceStamped):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = 0.0
        t.transform.rotation = msg.pose.pose.orientation
        self.last_transform = t
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = PoseToTf()
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