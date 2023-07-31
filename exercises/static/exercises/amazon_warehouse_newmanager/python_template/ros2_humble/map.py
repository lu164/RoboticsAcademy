import numpy as np
import math
from math import pi as pi
import cv2

class Map:
	def __init__(self, pose3d):
		self.pose3d = pose3d
	
	def RTx(self, angle, tx, ty, tz):
		RT = np.matrix([[1, 0, 0, tx], [0, math.cos(angle), -math.sin(angle), ty], 
						[0, math.sin(angle), math.cos(angle), tz], [0, 0, 0, 1]])
		return RT
		
	def RTy(self, angle, tx, ty, tz):
		RT = np.matrix([[math.cos(angle), 0, math.sin(angle), tx], [0, 1, 0, ty],
						[-math.sin(angle), 0, math.cos(angle), tz], [0, 0, 0, 1]])
		return RT
		
	def RTz(self, angle, tx, ty, tz):
		RT = np.matrix([[math.cos(angle), -math.sin(angle), 0, tx], [math.sin(angle), math.cos(angle), 0, ty],
						[0, 0, 1, tz], [0, 0, 0, 1]])
		return RT
		
	def RTVacuum(self):
		RTz = self.RTz(pi/2, 50, 70, 0)
		return RTz
		
	def getRobotCoordinates(self, pose):
		x = pose.x
		y = pose.y

		scale_x = 20.8; offset_x = 208
		x = scale_x * y + offset_x

		scale_y = 19.64; offset_y = 137
		y = scale_y * x + offset_y
		
		print(" - Coordinate: " + str(x) + ", " + str(y))
		print(" -> pose: " + str(pose))
		
		return x, y

	def getRobotAngle(self, pose):
		rt = pose.yaw

		ty = math.cos(-rt) - math.sin(-rt)
		tx = math.sin(-rt) + math.cos(-rt)

		print(" - Angle: " + str(tx) + ", " + str(ty))
		print(" -> rt: " + str(rt))

		return tx, ty

	# Function to reset
	def reset(self):
		# Nothing to do, service takes care!
		pass
	
