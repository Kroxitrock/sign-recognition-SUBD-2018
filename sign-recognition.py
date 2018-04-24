# import the necessary packages
import cv2
import time
import numpy as np
import imutils
from imutils.video import VideoStream
from imutils.video import FPS
from multiprocessing import Process
from multiprocessing import Queue
import re

try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def modify_value(st):
	st = st.replace(' ', '')
	st = st.replace('o', '0')
	st = st.replace('O', '0')
	st = re.sub("[^0-9]", "", st)
	if len(st) == 1:
		st += str(0)

	end=st[-1:len(st)]
	if end != 0:
		st = st[:-1]
		st += str(0)		

	return st

def classify_frame(inputQueue, outputQueue):
	# keep looping
	while True:
		# check to see if there is a frame in our input queue
		if not inputQueue.empty():
			# grab the frame from the input queue, resize it, and
			# construct a blob from it
			crop = inputQueue.get()
			
			value = pytesseract.image_to_string(Image.fromarray(crop))
			value = modify_value(value)
			
			# write the detections to the output queue
			outputQueue.put(value)


# initialize the input queue (frames), output queue (detections),
# and the list of actual detections returned by the child process
inputQueue = Queue(maxsize=1)
outputQueue = Queue(maxsize=1)
value = 50
# construct a child process *indepedent* from our main process of
# execution
print("[INFO] starting process...")
p = Process(target=classify_frame, args=( inputQueue,
	outputQueue,))
p.daemon = True
p.start()

max_speed = 50;

print("[INFO] starting video stream...")
vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

while True:
	# grab the frame from the threaded video stream, resize it, and
	# grab its imensions
	frame = vs.read()
	frame = imutils.resize(frame, width=400)
	(fH, fW) = frame.shape[:2]
	
	output = frame.copy

	cimg = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	circles = cv2.HoughCircles(cimg,cv2.HOUGH_GRADIENT, 1.2, 100)


	if circles is not None:
		# convert the (x, y) coordinates and radius of the circles to integers
		circles = np.round(circles[0, :]).astype("int")
	 
		# loop over the (x, y) coordinates and radius of the circles
		for (x, y, r) in circles:
			try:
				crop = frame[(y-r):(y+r),(x-r):(x+r)]
			except:
				print('Crop error')			
			cv2.imshow('Cropped', crop)
			if inputQueue.empty():
				inputQueue.put(crop)

	# if the output queue *is not* empty, grab the detections
	if not outputQueue.empty():
		value = outputQueue.get()
	if int(value) != 0:
		max_speed = value;
	
	print('#####################################'  )
	print(' max speed:' + str(max_speed) + ' detected_value:' + str(value))
	print('#####################################'  )
	cv2.imshow("output", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break

