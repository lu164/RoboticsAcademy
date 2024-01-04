import json
import cv2
import base64
import threading
import time
from datetime import datetime
import subprocess
import websocket
import numpy as np
from shared.image import SharedImage
from interfaces.pose3d import ListenerPose3d
import re
import os
from map import MAP


# Graphical User Interface Class
class GUI:
    # Initialization function
    # The actual initialization
    def __init__(self, host, hal):
    

        self.payload = {'image': '', 'map': '', 'array': ''}
        self.server = None
        self.client = None

        self.host = host

        self.shared_image = SharedImage("numpyimage")
        
        self.array_lock = threading.Lock()
        self.array = None

        self.acknowledge = False
        self.acknowledge_lock = threading.Lock()

        self.mapXY = None
        self.worldXY = None
        # Take the console object to set the same websocket and client
        self.hal = hal
        

        # Create the lap object
        self.pose3d_object = ListenerPose3d("/taxi_holo/odom")
        self.map = MAP(self.pose3d_object)

        self.client_thread = threading.Thread(target=self.run_websocket)
        self.client_thread.start()

    def run_websocket(self):
        while True:
            self.client = websocket.WebSocketApp('ws://127.0.0.1:2303',
                                                 on_message=self.on_message,)
            self.client.run_forever(ping_timeout=None, ping_interval=0)


    # Function to get value of Acknowledge
    def get_acknowledge(self):
        self.acknowledge_lock.acquire()
        acknowledge = self.acknowledge
        self.acknowledge_lock.release()

        return acknowledge

    # Function to get value of Acknowledge
    def set_acknowledge(self, value):
        self.acknowledge_lock.acquire()
        self.acknowledge = value
        self.acknowledge_lock.release()

    # encode the image data to be sent to websocket
    def payloadImage(self):
        image = self.shared_image.get()
        payload = {'image': '', 'shape': ''}
    	
        shape = image.shape
        frame = cv2.imencode('.PNG', image)[1]
        encoded_image = base64.b64encode(frame)
        
        payload['image'] = encoded_image.decode('utf-8')
        payload['shape'] = shape
        
        return payload

    def showNumpy(self, image):
        processed_image = np.stack((image,) * 3, axis=-1)
        self.shared_image.add(processed_image)

    # Process the array(ideal path) to be sent to websocket
    def showPath(self, array):
        self.array_lock.acquire()

        strArray = ''.join(str(e) for e in array)

        # Remove unnecesary spaces in the array to avoid JSON syntax error in javascript
        strArray = re.sub(r"\[[ ]+", "[", strArray)
        strArray = re.sub(r"[ ]+", ", ", strArray)
        strArray = re.sub(r",[ ]+]", "]", strArray)
        strArray = re.sub(r",,", ",", strArray)
        strArray = re.sub(r"]\[", "],[", strArray)
        strArray = "[" + strArray + "]"

        self.array = strArray
        self.array_lock.release()

    def getTargetPose(self):
        if (self.worldXY != None):
            return [self.worldXY[1], self.worldXY[0]]
        else:
            return None

    # Update the gui
    def update_gui(self):
        # Payload Image Message
        payload = self.payloadImage()
        self.payload["image"] = json.dumps(payload)

        self.payload["array"] = self.array
        # Payload Map Message
        pos_message1 = self.map.getTaxiCoordinates()
        # print(self.pose3d_object.getPose3d())
        ang_message = self.map.getTaxiAngle()
        pos_message = str(pos_message1 + ang_message)
        # print("pos2 : {} ,  ang : {}".format(pos_message,ang_message))
        self.payload["map"] = pos_message

        message = json.dumps(self.payload)
        if self.client:
            try:
                self.client.send(message)
            except Exception as e:
                print(f"Error sending message: {e}")


        return list(pos_message1)


    def on_message(self, ws, message):
        """Handles incoming messages from the websocket client."""s
        if message.startswith("#ack"):
            self.set_acknowledge(True)

        elif (message[:5] == "#pick"):
            data = eval(message[5:])
            self.mapXY = data
            x, y = self.mapXY
            worldx, worldy = self.map.gridToWorld(x, y)
            self.worldXY = [worldx, worldy]
            print("World : {}".format(self.worldXY))


    # Function to reset
    def reset_gui(self):
        self.map.reset()

# This class decouples the user thread
# and the GUI update thread
class ThreadGUI:
    """Class to manage GUI updates and frequency measurements in separate threads."""

    def __init__(self, gui):
        """Initializes the ThreadGUI with a reference to the GUI instance."""
        self.gui = gui
        self.ideal_cycle = 80
        self.real_time_factor = 0
        self.frequency_message = {'brain': '', 'gui': '', 'rtf': ''}
        self.iteration_counter = 0
        self.running = True

    def start(self):
        """Starts the GUI, frequency measurement, and real-time factor threads."""
        self.frequency_thread = threading.Thread(target=self.measure_and_send_frequency)
        self.gui_thread = threading.Thread(target=self.run)
        self.rtf_thread = threading.Thread(target=self.get_real_time_factor)
        self.frequency_thread.start()
        self.gui_thread.start()
        self.rtf_thread.start()
        print("GUI Thread Started!")

    def get_real_time_factor(self):
        """Continuously calculates the real-time factor."""
        while True:
            time.sleep(2)
            args = ["gz", "stats", "-p"]
            stats_process = subprocess.Popen(args, stdout=subprocess.PIPE)
            with stats_process.stdout:
                for line in iter(stats_process.stdout.readline, b''):
                    stats_list = [x.strip() for x in line.split(b',')]
                    self.real_time_factor = stats_list[0].decode("utf-8")

    def measure_and_send_frequency(self):
        """Measures and sends the frequency of GUI updates and brain cycles."""
        previous_time = datetime.now()
        while self.running:
            time.sleep(2)
            current_time = datetime.now()
            dt = current_time - previous_time
            ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
            previous_time = current_time
            measured_cycle = ms / self.iteration_counter if self.iteration_counter > 0 else 0
            self.iteration_counter = 0
            brain_frequency = round(1000 / measured_cycle, 1) if measured_cycle != 0 else 0
            gui_frequency = round(1000 / self.ideal_cycle, 1)
            self.frequency_message = {'brain': brain_frequency, 'gui': gui_frequency, 'rtf': self.real_time_factor}
            message = json.dumps(self.frequency_message)
            if self.gui.client:
                try:
                    self.gui.client.send(message)
                except Exception as e:
                    print(f"Error sending frequency message: {e}")

    def run(self):
        """Main loop to update the GUI at regular intervals."""
        while self.running:
            start_time = datetime.now()
            self.gui.update_gui()
            self.iteration_counter += 1
            finish_time = datetime.now()
            dt = finish_time - start_time
            ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
            sleep_time = max(0, (50 - ms) / 1000.0)
            time.sleep(sleep_time)

