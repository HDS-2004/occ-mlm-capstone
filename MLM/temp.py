import cv2
from cv2.typing import NumPyArrayNumeric
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
import scipy.stats as stats
import math
from level_identifier import get_the_four_levels
cap = cv2.VideoCapture('captured_video/data.MOV')

if not cap.isOpened():
    print("Video error")
    exit()




i = 0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_buffer = []
while(i < total_frames):
    ret, frame = cap.read()
    if not ret:
        break
    frame_buffer.append(frame)
cap.release()







frame = frame_buffer[82]
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(2, 2))
img_clahe = clahe.apply(gray)
gray = cv2.GaussianBlur(gray, (3, 21), 0)
tmp = cv2.inRange(gray, 160, 230)
cv2.imshow('frame',tmp) #use this to see what the row detector is seeing when its trying to spot the 255 pulse that indicates header start
cv2.waitKey(0)
tmp = tmp[697:]
cv2.imshow('frame',tmp) #use this to see what the row detector is seeing when its trying to spot the 255 pulse that indicates header start
cv2.waitKey(0)
