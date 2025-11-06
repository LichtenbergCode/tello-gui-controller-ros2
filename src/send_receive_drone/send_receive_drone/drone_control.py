
 ####################################
## Executable name: drone_gui       ##
## Author: Alberto Lombera Vélez    ##
## Date: 30/03/2025                 ##
## License: ???                     ##
 ####################################

import cv2
import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor, MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup, MutuallyExclusiveCallbackGroup
from djitellopy import tello
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from drone_interface.msg import DroneStatus
from drone_interface.msg import DroneSpeed
from drone_interface.srv import DroneAction

from time import sleep

class  DroneClass:
    def __init__(self, drone_args):
        self.drone_args = drone_args
        self.connected = False
        self.speed = 50
        self.battery = 50
        self.temperature = 50.0
        self.drone = tello.Tello()
        self.create_control_node()
    
    def create_control_node(self):
        rclpy.init(args = self.drone_args)
        self.drone_control_node = DroneControllNode(self)
        self.drone_status_node = DroneGetTempBatt(self.get_battery_temperature)
        self.img_node = DroneCamaraNode(self.get_image)
        self.executor = MultiThreadedExecutor()
        #self.executor = SingleThreadedExecutor()
        self.executor.add_node(self.drone_control_node)
        self.executor.add_node(self.drone_status_node)
        self.executor.add_node(self.img_node)
        self.executor.spin()
        rclpy.shutdown()
    
    def connect(self):
        try:
            self.drone.connect()
            self.drone.streamon()
            sleep(1)
            
            self.connected = True
            return True
        except:
            return False
    
    def get_speed(self, msg):
        self.speed = msg
    
    def get_battery_temperature(self):
        
        if self.connected:
            self.battery=self.drone.get_battery()
            self.temperature = self.drone.get_temperature()

        return self.battery, self.temperature
    
    def get_image(self):
        if self.connected:
            
            self.frame = self.drone.get_frame_read().frame
            msg = True
        else: 
            self.frame = None
            msg = False

        return self.frame, msg

    def send(self, action):
        lr, fb, up, yv = 0, 0, 0, 0
        message = False
        
        if action == 'CONNECT':
            self.connect()

        if self.connected:
            match action:
                case 'FORWARD':
                    fb = self.speed
                    message = True
                case 'BACKWARD':
                    fb = -self.speed
                    message = True
                case 'LEFT':
                    lr = -self.speed
                    message = True
                case 'RIGHT':
                    lr = self.speed
                    message = True
                case 'TURNL':
                    yv = -self.speed
                    message = True
                case 'TURNR':
                    yv = self.speed
                    message = True
                case 'UP':
                    up = self.speed
                    message = True
                case 'DOWN':
                    up = -self.speed
                    message = True
                case 'TKOF':
                    if not self.drone.is_flying:
                        try:
                            self.drone.takeoff()
                            message = True
                            sleep(1.5)
                        except: 
                            message = False
                    else: 
                        message = False
                case 'LAND':
                    if self.drone.is_flying:
                        try:
                            self.drone.land()
                            message = True
                        except:
                            message = False
                    else: 
                        message = False
                case 'CONNECT':
                    self.connect()

                case _:
                    message = True

            if self.drone.is_flying:
                try:
                    self.drone.send_rc_control(lr, fb, up, yv)
                    message = True
                except:
                    message = False
            else:
                message = False
        return message

class DroneControllNode(Node):
    def __init__(self, drone):
        super().__init__("drone_control")
        self.drone = drone
        self.cb_group = ReentrantCallbackGroup()
        #Creating a server for control the drone
        self.server_ = self.create_service(DroneAction, 
                                           "drone_send",
                                           self.drone_action_callback,
                                           callback_group = self.cb_group)
        
        #Creating Subscriber
        self.subscriber_ = self.create_subscription(DroneSpeed,
                                                    "get_speed", 
                                                    self.subscriber_callback, 
                                                    10,
                                                    callback_group = self.cb_group)

        self.get_logger().info("Drone Control Node Has Been Started")

        
    def drone_action_callback(self, request = DroneAction.Request, response = DroneAction.Response):
        response.message = self.drone.send(request.action)
        return response
    
    def subscriber_callback(self, msg:DroneSpeed):
        self.drone.get_speed(msg.speed)

class DroneGetTempBatt(Node):
    def __init__(self, get_status):
        super().__init__('drone_get_temp_batt')
        self.get_status = get_status
        self.cb_group = MutuallyExclusiveCallbackGroup()
        self.publisher_ = self.create_publisher(DroneStatus, 'drone_get_status', 10, callback_group=self.cb_group)
        self.timer_ = self.create_timer(2.5, self.get_temp_batt, callback_group= self.cb_group)
        self.get_logger().info("Drone Get Temp Batt Has Been Started")
    
    def get_temp_batt(self):
        status_object = DroneStatus()
        status_object.battery, status_object.temperature = self.get_status()
        self.get_status()
        self.publisher_.publish(status_object)

class DroneCamaraNode(Node):
    def __init__(self, get_frame):
        super().__init__('drone_camara_publisher')
        self.get_frame = get_frame
        self.bridge_object = CvBridge()
        self.cb_group = MutuallyExclusiveCallbackGroup()
        self.publisher_ = self.create_publisher(Image, 'camara_img', 20, callback_group=self.cb_group)
        self.timer_ = self.create_timer(0.1, self.timer_callback, callback_group=self.cb_group)
        self.get_logger().info('Drone Camara Publisher Has Been Started')

    def timer_callback(self):
        img, condition = self.get_frame()
        if condition:
            img = cv2.resize(img, (0, 0), fx = 0.5, fy=0.5, interpolation = cv2.INTER_AREA)
            brg_image = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img_msg = self.bridge_object.cv2_to_imgmsg(brg_image)
            self.publisher_.publish(img_msg)

def main(args = None):
    DroneClass(args)
