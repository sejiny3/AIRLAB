"""ArUco marker detector: camera image -> TF frame per marker.

Subscribes /camera/image_raw (rgb8) and /camera/camera_info, detects DICT_4X4_50
markers, estimates each pose with solvePnP (marker side lengths per id) and
broadcasts <camera_frame> -> aruco_<id> stamped with the image time. The marker
frame follows OpenCV: z out of the marker face, x to the marker's right.
An annotated, half-size copy of the image goes to /aruco/debug_image (rgb8, for RViz)
and /aruco/debug_image/compressed (JPEG, for the web dashboard).

  ros2 run unbolt_manipulation aruco_detector --ros-args -p use_sim_time:=true
"""

import array

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, CompressedImage, Image
from tf2_ros import TransformBroadcaster


def rotation_to_quat(R):
    """3x3 rotation matrix -> (x, y, z, w)."""
    w = np.sqrt(max(0.0, 1.0 + R[0, 0] + R[1, 1] + R[2, 2])) / 2.0
    x = np.sqrt(max(0.0, 1.0 + R[0, 0] - R[1, 1] - R[2, 2])) / 2.0
    y = np.sqrt(max(0.0, 1.0 - R[0, 0] + R[1, 1] - R[2, 2])) / 2.0
    z = np.sqrt(max(0.0, 1.0 - R[0, 0] - R[1, 1] + R[2, 2])) / 2.0
    x = np.copysign(x, R[2, 1] - R[1, 2])
    y = np.copysign(y, R[0, 2] - R[2, 0])
    z = np.copysign(z, R[1, 0] - R[0, 1])
    return float(x), float(y), float(z), float(w)


class ArucoDetector(Node):
    def __init__(self):
        super().__init__('aruco_detector')
        # boxes 7 / 8 / 9 (red / green / blue), place spots 1-3 (work table) and N1 / N2 (supply table N)
        self.declare_parameter('marker_ids', [7, 8, 9, 1, 2, 3, 11, 12, 21, 22, 31, 32])
        self.declare_parameter('marker_sizes', [0.0375] * 3 + [0.075] * 9)  # black-border side length [m]
        self.declare_parameter('publish_debug_image', True)
        ids = self.get_parameter('marker_ids').value
        sizes = self.get_parameter('marker_sizes').value
        self.sizes = dict(zip(ids, sizes))
        self.debug = self.get_parameter('publish_debug_image').value

        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.params = cv2.aruco.DetectorParameters_create()
        self.params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.K = None
        self.tf = TransformBroadcaster(self)
        self.debug_pub = self.create_publisher(Image, '/aruco/debug_image', 2)
        self.debug_jpeg_pub = self.create_publisher(CompressedImage, '/aruco/debug_image/compressed', 2)
        self.create_subscription(CameraInfo, '/camera/camera_info', self._on_info, 2)
        self.create_subscription(Image, '/camera/image_raw', self._on_image, 2)
        self.get_logger().info(f'detecting markers {self.sizes}')

    def _on_info(self, msg):
        self.K = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        self.dist = np.array(msg.d, dtype=np.float64)

    def _on_image(self, msg):
        if self.K is None or msg.encoding != 'rgb8':
            return
        rgb = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.width, 3)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(gray, self.dictionary, parameters=self.params)

        found = []
        if ids is not None:
            for c, marker_id in zip(corners, ids.ravel().tolist()):
                size = self.sizes.get(marker_id)
                if size is None:
                    continue
                rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers([c], size, self.K, self.dist)
                R, _ = cv2.Rodrigues(rvecs[0][0])
                t = TransformStamped()
                t.header = msg.header
                t.child_frame_id = f'aruco_{marker_id}'
                t.transform.translation.x, t.transform.translation.y, t.transform.translation.z = map(float, tvecs[0][0])
                (t.transform.rotation.x, t.transform.rotation.y,
                 t.transform.rotation.z, t.transform.rotation.w) = rotation_to_quat(R)
                self.tf.sendTransform(t)
                found.append((c, marker_id, rvecs[0][0], tvecs[0][0], size))

        if self.debug:
            vis = rgb.copy()
            for c, marker_id, rvec, tvec, size in found:
                cv2.aruco.drawDetectedMarkers(vis, [c], np.array([[marker_id]]))
                cv2.drawFrameAxes(vis, self.K, self.dist, rvec, tvec, size)
            small = cv2.resize(vis, (msg.width // 2, msg.height // 2), interpolation=cv2.INTER_AREA)
            out = Image()
            out.header = msg.header
            out.height, out.width = small.shape[:2]
            out.encoding = 'rgb8'
            out.step = out.width * 3
            out.data = array.array('B', small.tobytes())  # bytes would be validated per element
            self.debug_pub.publish(out)

            ok, jpeg = cv2.imencode('.jpg', cv2.cvtColor(small, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                comp = CompressedImage()
                comp.header = msg.header
                comp.format = 'jpeg'
                comp.data = array.array('B', jpeg.tobytes())
                self.debug_jpeg_pub.publish(comp)


def main():
    rclpy.init()
    node = ArucoDetector()
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
