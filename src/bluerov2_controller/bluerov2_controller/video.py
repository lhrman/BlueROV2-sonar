import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
import subprocess
import os
import time
import glob

from bluerov2_interfaces.srv import CaptureImage


class CaptureImageService(Node):

    def __init__(self):
        super().__init__('capture_image_service')

        self.srv = self.create_service(CaptureImage, 'capture_image', self.capture_image_callback)
        package_share_directory = os.path.join(
            os.path.dirname(__file__), 'bluerov2_captured_images')
        self.image_directory = os.path.abspath(package_share_directory)
        os.makedirs(self.image_directory, exist_ok=True)
        self.image_pattern = 'image-%05d.jpg'
        self.full_pattern = os.path.join(self.image_directory, self.image_pattern)
        self.image_counter = 1
        self.gstream_initi_time = 1.0 # in seconds


    def capture_image_callback(self, request, response):
        self.get_logger().info(f'Received capture image request with extension {request.image_name}')

        try:
            gst_command = [
                'timeout', f'{self.gstream_initi_time}', 'gst-launch-1.0', 'udpsrc', 'port=5600', '!', 'application/x-rtp, payload=96', '!',
                'rtph264depay', '!', 'avdec_h264', '!', 'videoconvert', '!', 'jpegenc', '!',
                'multifilesink', f'location={self.full_pattern}'
            ]
            
            # Start the GStreamer process
            process = subprocess.Popen(gst_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait until the process completes
            stdout, stderr = process.communicate()

            # Check if process was successful
            if process.returncode not in [0, 124]:  # 124 is the exit code for timeout
                self.get_logger().error(f'GStreamer process failed: {stderr.decode()}')
                response.success = False
                response.message = 'Failed to capture image'
                return response
            
            # Keep only the last image
            image_files = sorted(glob.glob(os.path.join(self.image_directory, 'image-*.jpg')))
            if image_files:
                latest_image = image_files[-1]
                final_image = os.path.join(self.image_directory, f'image_{self.image_counter}__{request.image_name}.jpg')
                os.rename(latest_image, final_image)
                self.get_logger().info(f'Image {self.image_counter}__{request.image_name} captured successfully')
                response.success = True
                response.message = f'Image {self.image_counter}__{request.image_name} captured successfully'
                self.image_counter += 1  # Increment the image counter
            else:
                self.get_logger().error('Failed to find any images')
                response.success = False
                response.message = 'Failed to find any images'

            # Clean up other images
            for file_path in image_files[:-1]:  # Keep only the latest image
                os.remove(file_path)
                
        except subprocess.CalledProcessError as e:
            self.get_logger().error(f'Failed to capture image: {e}')
            response.success = False
            response.message = 'Failed to capture image'
        finally:
            # Ensure the GStreamer process is terminated
            if process and process.poll() is None:
                process.terminate()
                process.wait()
        
        return response

def main(args=None):
    rclpy.init(args=args)
    node = CaptureImageService()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()