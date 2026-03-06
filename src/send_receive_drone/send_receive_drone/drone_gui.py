
 ####################################
## Executable name: drone_gui       ##
## Author: Alberto Lombera Vélez    ##
## Date: 30/03/2025                 ##
## License: ???                     ##
 ####################################

from ttkbootstrap.constants import *
import ttkbootstrap as ttk
import threading 

from PIL import ImageTk, ImageOps
from PIL import Image as PILImage
import numpy as np
from time import sleep 
from sys import exit
from pynput.keyboard import Key, Listener
from functools import partial

import cv2
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from rclpy.executors import SingleThreadedExecutor, MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup, MutuallyExclusiveCallbackGroup
from drone_interface.msg import DroneStatus
from drone_interface.msg import DroneSpeed
from drone_interface.srv import DroneAction

class Window(ttk.Window):
    def __init__(self, size, name, ros_args):
        super().__init__(themename = 'sandstone') #sandstone
        self.ros_args = ros_args
        self.geometry(f'{size[0]}x{size[1]}')
        self.title(name)
        self.resizable(False, False)
        self.columnconfigure((0,1), weight = 1, uniform = 'a')
        self.rowconfigure((0,1), weight = 1, uniform = 'a')
        self.left_button_pressed = False
        self.img_capture = False
        self.status1 = 'NONE'
        self.status2 = 'NONE'
        self.status3 = 'NONE'
        ########## CALLING METHODS ##########
        self.menu()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.creating_widgets()
        self.creating_video()

        ########## Threading ##########
        thread1 = threading.Thread(target = self.keyboard_events, daemon = True)
        thread2 = threading.Thread(target = self.ros_nodes, daemon= True)
        thread1.start()
        thread2.start()
        ########## Loop ##########
        self.mainloop()

    def menu(self):
        self.menu = ttk.Menu()

        #sub menu 
        self.file_menu = ttk.Menu(self.menu, tearoff = False)
        self.button_take_of = self.file_menu.add_command(label = 'Take Of', command = lambda:self.menu_events('TKOF'))
        self.button_Land = self.file_menu.add_command(label = 'Land', command = lambda:self.menu_events('LAND'))
        self.button_connect = self.file_menu.add_command(label = 'Connect', command = lambda: self.menu_events('CONNECT'))
        self.menu.add_cascade(label = 'Drone', menu = self.file_menu)
        # running the menu 
        self.configure(menu = self.menu)
    
    def menu_events(self, variable):
        self.status3 = variable
        self.drone_control_srv_node.call_drone_control(self.status3)
        sleep(1.0)
        self.status3 = 'NONE'
        self.drone_control_srv_node.call_drone_control(self.status3)

    def creating_widgets(self):

        self.direction = FrameControl(self,
                                        'primary',
                                        './src/send_receive_drone/send_receive_drone/Images/forward.png',
                                        './src/send_receive_drone/send_receive_drone/Images/left.png',
                                        './src/send_receive_drone/send_receive_drone/Images/right.png',
                                        './src/send_receive_drone/send_receive_drone/Images/backward.png',
                                        'FORWARD',
                                        'LEFT',
                                        'RIGHT',
                                        'BACKWARD',
                                        self.send_drone_gui_buttons)
        self.direction.grid(column=1, row = 1, sticky = 'nswe')

        self.direction2 = FrameControl(self,
                                        'secondary',
                                        './src/send_receive_drone/send_receive_drone/Images/up2.png',
                                        './src/send_receive_drone/send_receive_drone/Images/one.png',
                                        './src/send_receive_drone/send_receive_drone/Images/second.png',
                                        './src/send_receive_drone/send_receive_drone/Images/down.png',
                                        'UP',
                                        'TURNL',
                                        'TURNR',
                                        'DOWN',
                                        self.send_drone_gui_buttons)
        
        self.direction2.grid(column = 0, row = 1, sticky = 'nswe')

        self.indicators = FrameIndicator(self, 50, 70)
        self.indicators.grid(column = 0, row = 0, sticky = 'nswe')

    def on_closing(self): # This is the routine that we're going to use at the moment that we close the window 

        self.quit()
        self.destroy()
        print('Good Bye')
        exit

    def creating_video(self):
        self.frame_video = ttk.Frame()
        self.frame_video.grid(row=0, column=1, sticky='nswe')
        self.label_video= ttk.Label(self.frame_video)
        self.label_video.place(anchor = CENTER,  relx = 0.5, rely = 0.5)
        self.update()

    def update(self):
        #img = frame
        if self.img_capture:
            img = PILImage.fromarray(self.frame)
            self.photo = ImageTk.PhotoImage(image = img)
            self.label_video.configure(image = self.photo) 
        self.after(15, self.update)
    
    def get_img(self, frame):
        self.frame = frame
        self.img_capture = True

    def update_indicators(self, battery, temperature):
        self.indicators.meter_temp.configure(amountused = temperature)
        self.indicators.meter_battery.configure(amountused = battery)
    
    def keyboard_events(self):
        def on_press(key):
            if key == Key.space:
                print('SPACE')
            elif key == Key.up:
                self.status3 = 'FORWARD'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key == Key.down:
                self.status3 = 'BACKWARD'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key == Key.left:
                self.status3 = 'LEFT'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key == Key.right:
                self.status3 = 'RIGHT'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key.char == 'a':
                self.status3 = 'TURNL'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key.char == 'd':
                self.status3 = 'TURNR'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key.char == 'w':
                self.status3 = 'UP'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key.char == 's':
                self.status3 = 'DOWN'
                self.drone_control_srv_node.call_drone_control(self.status3)
        
        def on_release(key):
            if key == Key.space:
                print('SPACE RELEASE')
            elif key == Key.up:
                self.status3 = 'NONE'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key == Key.down:
                self.status3 = 'NONE'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key == Key.left:
                self.status3 = 'NONE'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key == Key.right:
                self.status3 = 'NONE'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key.char == 'a':
                self.status3 = 'NONE'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key.char == 'd':
                self.status3 = 'NONE'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key.char == 'w':
                self.status3 = 'NONE'
                self.drone_control_srv_node.call_drone_control(self.status3)
            elif key.char == 's':
                self.status3 = 'NONE'
                self.drone_control_srv_node.call_drone_control(self.status3)
        
        with Listener(on_press = on_press, on_release=on_release) as listener:  
            listener.join()

    def get_speed(self):
        return self.indicators.speed2
    
    def send_drone_gui_buttons(self, variable):
        self.drone_control_srv_node.call_drone_control(variable)

    def ros_nodes(self):
        rclpy.init(args = self.ros_args)
        self.drone_control_srv_node = DroneControllClientNode(self.get_speed)
        self.drone_status_node = DroneGetStatusNode(self.update_indicators)
        self.drone_get_image_node = SubscriberGetImageNode(self.get_img) 
        self.executor = MultiThreadedExecutor()
        self.executor.add_node(self.drone_control_srv_node)
        self.executor.add_node(self.drone_status_node)
        self.executor.add_node(self.drone_get_image_node)
        self.executor.spin()
        rclpy.shutdown()

class FrameControl(ttk.Frame):
    def __init__(self, 
            root, 
            button_style, 
            path_button1, 
            path_button2, 
            path_button3, 
            path_button4,
            command_button1,
            command_button2,
            command_button3,
            command_button4,
            send_drone):
        super().__init__(master = root)

        self.button_style = button_style
        self.path_button1 = path_button1
        self.path_button2 = path_button2
        self.path_button3 = path_button3
        self.path_button4 = path_button4
        self.command1 = command_button1
        self.command2 = command_button2
        self.command3 = command_button3
        self.command4 = command_button4
        self.send_drone = send_drone
        self.command_not_info = 'NONE'
        self.send_info = 'NONE'
        self.root = root
        

        self.columnconfigure((0, 4), weight = 2, uniform='a')
        self.columnconfigure(2, weight = 9, uniform = 'a')
        self.columnconfigure((1,3), weight = 7, uniform = 'a')

        self.rowconfigure((0, 5), weight = 1, uniform = 'a')
        self.rowconfigure((1, 4), weight = 3, uniform = 'a')
        self.rowconfigure((2, 3), weight = 4, uniform = 'a')

        self.images()
        self.buttons()
        self.events()

    def images(self):
        # Images # 
        image_first_button = PILImage.open(self.path_button1).resize((70, 70))
        image_second_button = PILImage.open(self.path_button2).resize((70, 70))
        image_third_button = PILImage.open(self.path_button3).resize((70, 70))
        image_fourth_button = PILImage.open(self.path_button4).resize((70, 70))

        self.image_first_button_tk = ImageTk.PhotoImage(image_first_button)
        self.image_second_button_tk = ImageTk.PhotoImage(image_second_button)
        self.image_third_button_tk = ImageTk.PhotoImage(image_third_button)
        self.image_fourth_button_tk = ImageTk.PhotoImage(image_fourth_button)

        self.left_button_pressed = False
        
    def buttons(self):
        self.button_1 = ttk.Button(self, 
                                    image = self.image_first_button_tk, 
                                    bootstyle = self.button_style) 
        
        self.button_2 = ttk.Button(self, 
                                    image = self.image_second_button_tk, 
                                    bootstyle = self.button_style)
        
        self.button_3 = ttk.Button(self, 
                                    image = self.image_third_button_tk, 
                                    bootstyle = self.button_style)
        
        self.button_4 = ttk.Button(self, 
                                    image = self.image_fourth_button_tk, 
                                    bootstyle = self.button_style)

        # grid
        self.button_1.grid(column = 2, row = 1, sticky = 'nswe', rowspan = 2, padx=8, pady = 5)
        self.button_2.grid(column = 1, row = 2, sticky = 'nswe', rowspan = 2)
        self.button_3.grid(column = 3, row =  2, sticky = 'nswe', rowspan = 2)
        self.button_4.grid(column = 2, row = 3, sticky = 'nswe', rowspan = 2, padx=8, pady = 5)

    def events(self):
        self.button_1.bind('<ButtonPress-1>', lambda _: self.event_func(self.command1))
        self.button_2.bind('<ButtonPress-1>', lambda _: self.event_func(self.command2))
        self.button_3.bind('<ButtonPress-1>', lambda _: self.event_func(self.command3))
        self.button_4.bind('<ButtonPress-1>', lambda _: self.event_func(self.command4))

        self.button_1.bind('<ButtonRelease-1>', lambda _: self.event_func(self.command_not_info))
        self.button_2.bind('<ButtonRelease-1>', lambda _: self.event_func(self.command_not_info))
        self.button_3.bind('<ButtonRelease-1>', lambda _: self.event_func(self.command_not_info))
        self.button_4.bind('<ButtonRelease-1>', lambda _: self.event_func(self.command_not_info))

    def event_func(self, variable):
        self.send_info = variable
        self.send_drone(variable)

class FrameIndicator(ttk.Frame):
    def __init__(self, root, value1, value2):
        super().__init__(master = root)

        self.temperature = ttk.IntVar
        self.temperature = value1
        self.battery = ttk.IntVar
        self.battery = value2

        self.columnconfigure((1, 3, 5), weight = 1, uniform = 'a')
        self.columnconfigure((2, 4), weight = 28, uniform = 'a')
        self.rowconfigure((0, 3), weight = 1, uniform = 'a')
        self.rowconfigure(2, weight = 4, uniform = 'a')
        self.rowconfigure((1), weight = 10, uniform = 'a')
        self.creating_widgets()

    def creating_widgets(self):

        self.meter_temp = ttk.Meter(
                        self,
                        textright = '°C',
                        amounttotal = 100,
                        amountused =  0,
                        #stripethickness = 2,
                        interactive = False,
                        metertype = 'semi', #'full'
                        bootstyle = 'danger',
                        subtext = "")
        self.meter_temp.grid(column = 4, row = 1, sticky = 'nswe')

        self.meter_battery = ttk.Meter(
                        self,
                        textright = '%',
                        amounttotal = 100,
                        amountused = self.battery,
                        interactive = False,
                        metertype = 'semi', #'full'
                        bootstyle = 'success')
        self.meter_battery.grid(column = 2, row = 1, sticky = 'nswe')


        self.speed = ttk.IntVar(value = 50)
        self.scale = ttk.Scale(self, from_ = 0, 
                                to = 100, 
                                variable = self.speed, 
                                command = lambda _: self.scale_variable())
        self.scale.grid(column = 2, row = 2, rowspan = 3, sticky = NSEW)
        self.scale_variable()
    
    def scale_variable(self):
        self.speed2 = self.speed.get()
        label = ttk.Label(self, 
                            text = f'Speed = {self.speed2}', 
                            anchor = 'center',
                            font = "Calibri 18 bold")
        label.grid(column = 4, row = 2, sticky = 'nswe')

class DroneControllClientNode(Node):
    def __init__(self, get_speed):
        super().__init__('drone_gui')
        self.get_speed = get_speed
        self.cb_group = ReentrantCallbackGroup()

        self.client_ = self.create_client(DroneAction, "drone_send", callback_group = self.cb_group)
        self.timer_ = self.create_timer (2.0, self.callback_timer, self.cb_group)
        self.publisher_ = self.create_publisher(DroneSpeed, "get_speed", 10, callback_group=self.cb_group)

        self.get_logger().info("Drone Control Node Service Has Been Started")

    def callback_timer(self):
        speed_object = DroneSpeed()
        speed_object.speed = self.get_speed()
        self.publisher_.publish(speed_object)

    def call_drone_control(self, action):
        while not self.client_.wait_for_service(1.0):
            self.get_logger().warn("Waiting for drone send server...")
        
        # Using the interface for request
        request = DroneAction.Request()
        request.action = action

        future = self.client_.call_async(request)
        future.add_done_callback(
            partial(self.callback_call_drone_control, request=request))

    def callback_call_drone_control(self, future, request):
        if not future.result().message:
            self.get_logger().info(f'Server Response: {future.result().message}')

class DroneGetStatusNode(Node):
    def __init__(self, show_in_gui):
        super().__init__("show_status_node")
        self.cb_group = ReentrantCallbackGroup()
        self.show_in_gui = show_in_gui
        self.status_object = DroneStatus()
        self.subscriber_ = self.create_subscription(DroneStatus, 'drone_get_status', self.show, 20, callback_group=self.cb_group)
        self.get_logger().info('Subscriber Show Status Has Been Started')

    def show(self, status:DroneStatus):
        self.show_in_gui(status.battery, status.temperature)

class SubscriberGetImageNode (Node):
    def __init__(self, show_img):
        super().__init__('subscriber_get_image')
        self.show = show_img
        self.bridge_object_ = CvBridge()
        self.cb_group = ReentrantCallbackGroup()
        self.subscription_ = self.create_subscription(Image, 'camara_img',self.listener_callback, 20, callback_group=self.cb_group)
        self.get_logger().info("Subscriber Get Image Has Been Started")

    def listener_callback (self, image_message):
        img = self.bridge_object_.imgmsg_to_cv2(image_message)
        self.show(img)

def main(args = None):
    root = Window((1300, 800), 'Drone Control', args)#1300, 800

if __name__ == '__main__': 
    main()