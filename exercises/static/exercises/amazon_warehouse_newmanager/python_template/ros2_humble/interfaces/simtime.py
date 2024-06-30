import rclpy
from rclpy.node import Node
from rosgraph_msgs.msg import Clock
import threading
from math import pi as PI
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

class SimTime():
    def __init__(self):
        self.sec = 0
        self.nanosec = 0
    
    def __str__(self):
        s = "SimTime: {\n   sec:" + str(self.sec) + "\n   nanosec: " + str(self.nanosec) + "\n}"
        return s
    
class ListenerSimTime(Node):
    '''
    ROS clock subscriber, clock client to receive simulated time from ROS nodes
    '''
    def __init__(self, topic):
        '''
        ListenerSimTime Constructor
        
        @param topic: ROS topic to subscribe
        
        @type topic: 
        '''

        super().__init__("simtime_subscriber_node")

        self.topic = topic
        self.data = SimTime()
        self.sub = None
        self.lock = threading.Lock()
        self.start()

    def __callback(self, clock):
        '''
        Callback function to receive and save the simulated time
        
        @param simtime: ROS Clock received
        
        @type simtime: Clock
        '''

        simtime = self.clock2SimTime(clock)

        self.lock.acquire()
        self.data = simtime
        self.lock.release()

    def start (self):
        '''
        Starts (subscribes) the client
        '''

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.sub = self.create_subscription(
            Clock, 
            self.topic, 
            self.__callback, 
            qos_profile=qos_profile)

    def stop(self):
        '''
        Stops (unregisters) the client
        '''

        self.sub.unregister()

    def clock2SimTime(self, clock):
        simtime = SimTime()
        simtime.sec = clock.clock.sec
        simtime.nanosec = clock.clock.nanosec

        return simtime
    
    def getSimTime(self):
        '''
        Returns last simulated time

        @return last JdeRobotTypes SimTime saved
        '''

        self.lock.acquire()
        simtime = self.data
        self.lock.release()

        return simtime