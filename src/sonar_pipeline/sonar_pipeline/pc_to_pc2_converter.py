#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud, PointCloud2, PointField
from std_msgs.msg import Header
from sensor_msgs_py import point_cloud2  # Make sure this is installed

class PointCloudConverter(Node):
    def __init__(self):
        super().__init__('pointcloud_converter')
        
        # Subscriber to the old PointCloud topic
        self.subscription = self.create_subscription(
            PointCloud,
            '/micron_sonar/point_cloud',  # <-- Your input topic
            self.listener_callback,
            10)
        
        # Publisher for the new PointCloud2 topic
        self.publisher = self.create_publisher(
            PointCloud2,
            '/micron_sonar/point_cloud2', # <-- Your output topic
            10)
        self.get_logger().info('PointCloud to PointCloud2 converter node started...')

    def listener_callback(self, pc_msg):
        
        # 1. Define the fields for the PointCloud2 message
        #    We always have x, y, z
        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        
        # 2. Prepare the points data list
        points_data = []
        
        # Check if we have additional channels (like 'intensity')
        if not pc_msg.channels:
            # Simple case: only XYZ
            for p in pc_msg.points:
                points_data.append([p.x, p.y, p.z])
        
        else:
            # Complex case: Handle channels. 
            # This example assumes one channel (e.g., intensity)
            # You may need to adapt this logic if you have more or different channels
            
            # Add the channel to our fields list
            channel_offset = 12  # After x, y, z (4*3=12 bytes)
            for channel in pc_msg.channels:
                # Assuming all channels are FLOAT32. Adapt if needed.
                fields.append(PointField(
                    name=channel.name,
                    offset=channel_offset,
                    datatype=PointField.FLOAT32,
                    count=1
                ))
                channel_offset += 4 # Increment offset for the next channel
            
            # Combine point data with channel data
            for i, p in enumerate(pc_msg.points):
                point_with_channels = [p.x, p.y, p.z]
                for channel in pc_msg.channels:
                    point_with_channels.append(channel.values[i])
                points_data.append(point_with_channels)

        # 3. Create the PointCloud2 header
        header = Header()
        header.stamp = pc_msg.header.stamp
        header.frame_id = pc_msg.header.frame_id
        
        # 4. Create the PointCloud2 message
        try:
            pc2_msg = point_cloud2.create_cloud(header, fields, points_data)
            
            # 5. Publish the new message
            self.publisher.publish(pc2_msg)
            self.get_logger().debug(f'Published PointCloud2 message with {len(points_data)} points.')
            
        except Exception as e:
            self.get_logger().error(f'Failed to create PointCloud2 message: {e}')


def main(args=None):
    rclpy.init(args=args)
    converter = PointCloudConverter()
    rclpy.spin(converter)
    
    converter.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()