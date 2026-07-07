import time

import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

OUTPUT_PATH = "/workspace/project/ros2_ws/latest_rgb.png"
SAVE_HZ = 1.0


class ImageListener(Node):
    def __init__(self):
        super().__init__("image_listener")
        self.bridge = CvBridge()
        self.count = 0
        self.last_saved = 0.0
        self.subscription = self.create_subscription(
            Image, "/rgb", self.on_image, qos_profile_sensor_data
        )

    def on_image(self, msg: Image):
        now = time.monotonic()
        if now - self.last_saved < 1.0 / SAVE_HZ:
            return
        self.last_saved = now

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        cv2.imwrite(OUTPUT_PATH, frame)
        self.count += 1
        self.get_logger().info(
            f"frame {self.count}: shape={frame.shape}, dtype={frame.dtype} -> {OUTPUT_PATH}"
        )


def main():
    rclpy.init()
    rclpy.spin(ImageListener())


if __name__ == "__main__":
    main()
