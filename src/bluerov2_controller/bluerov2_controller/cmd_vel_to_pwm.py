#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import UInt16

class CmdVelToPWM(Node):
    def __init__(self):
        super().__init__('cmd_vel_to_pwm')
        self.forward_pub = self.create_publisher(UInt16, '/bluerov2/rc/forward', 10)
        self.lateral_pub = self.create_publisher(UInt16, '/bluerov2/rc/lateral', 10)
        self.yaw_pub = self.create_publisher(UInt16, '/bluerov2/rc/yaw', 10)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_cb, 10)
        self.get_logger().info('CmdVelToPWM pokrenut.')

    def cmd_vel_cb(self, msg):
        forward_pwm = int(1500 + msg.linear.x * 400)
        lateral_pwm = int(1500 + msg.linear.y * 400)
        yaw_pwm = int(1500 + msg.angular.z * 400)

        forward_pwm = max(1100, min(1900, forward_pwm))
        lateral_pwm = max(1100, min(1900, lateral_pwm))
        yaw_pwm = max(1100, min(1900, yaw_pwm))

        self.forward_pub.publish(UInt16(data=forward_pwm))
        self.lateral_pub.publish(UInt16(data=lateral_pwm))
        self.yaw_pub.publish(UInt16(data=yaw_pwm))

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(CmdVelToPWM())

if __name__ == '__main__':
    main()