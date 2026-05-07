#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud, LaserScan
import numpy as np
import math

class PointCloudToLaserScan(Node):
    def __init__(self):
        super().__init__('pointcloud_to_laserscan')

        # Parametri - prilagodi ih po potrebi preko launch fajla ili komande
        self.declare_parameter('min_height', -0.5)
        self.declare_parameter('max_height',  0.5)
        self.declare_parameter('angle_increment', math.radians(1.0))
        self.declare_parameter('min_range', 1.0)
        self.declare_parameter('max_range', 5.0)

        self.min_height = self.get_parameter('min_height').value
        self.max_height = self.get_parameter('max_height').value
        self.angle_increment = self.get_parameter('angle_increment').value
        self.min_range = self.get_parameter('min_range').value
        self.max_range = self.get_parameter('max_range').value

        self.angle_min = -math.pi
        self.angle_max =  math.pi
        self.num_beams = int(round((self.angle_max - self.angle_min) / self.angle_increment))

        self.sub = self.create_subscription(
            PointCloud,
            '/micron_sonar/point_cloud',
            self.pc_callback,
            10)

        self.pub = self.create_publisher(LaserScan, '/scan', 10)
        self.pub_pc = self.create_publisher(PointCloud, '/micron_sonar/point_cloud_filtered', 10)
        self.get_logger().info(f"Sonar Converter pokrenut. Rezolucija: {self.num_beams} zraka.")

    def pc_callback(self, msg: PointCloud):
        if not msg.points:
            return

        # 1. Izvlačenje podataka
        xs = np.array([p.x for p in msg.points])
        ys = np.array([p.y for p in msg.points])
        zs = np.array([p.z for p in msg.points])

        # 2. Inicijalizacija LaserScan poruke
        scan = LaserScan()
        scan.header = msg.header # Ovo zadržava frame_id i timestamp
        scan.angle_min = self.angle_min
        scan.angle_max = self.angle_max
        scan.angle_increment = self.angle_increment
        scan.time_increment = 0.0
        scan.scan_time = 0.1
        scan.range_min = self.min_range
        scan.range_max = self.max_range

        ranges = np.full(self.num_beams, np.inf)

        # 3. Filtriranje po visini i rangu
        distances_all = np.sqrt(xs**2 + ys**2)
        mask = (
            (zs >= self.min_height) & (zs <= self.max_height) &
            (distances_all >= self.min_range) & (distances_all <= self.max_range)
        )
        
        valid_ys = ys[mask]
        distances = distances_all[mask]

        if distances.size == 0:
            return

        # 4. Izračun kutova
        angles = np.arctan2(valid_ys, xs[mask])

        # 5. Popunjavanje zraka (najbliža JAKA točka pobjeđuje)
        beam_indices = ((angles - self.angle_min) / self.angle_increment).astype(int)
        beam_indices = np.clip(beam_indices, 0, self.num_beams - 1)

        for i in range(len(distances)):
            idx = beam_indices[i]
            if distances[i] < ranges[idx]:
                ranges[idx] = float(distances[i])

        # 6. Slanje podataka
        scan.ranges = ranges.tolist()
        self.pub.publish(scan)

        # 7. Publish filtered PointCloud
        filtered_pc = PointCloud()
        filtered_pc.header = msg.header
        filtered_pc.points = [msg.points[i] for i in np.where(mask)[0]]
        filtered_pc.channels = [
            type(ch)(name=ch.name, values=[ch.values[i] for i in np.where(mask)[0]])
            for ch in msg.channels
        ] if msg.channels else []
        self.pub_pc.publish(filtered_pc)

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