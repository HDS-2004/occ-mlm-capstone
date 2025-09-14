import cv2
from cv2.typing import NumPyArrayNumeric
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
import scipy.stats as stats
import math
# from level_identifier import get_the_four_levels
levels = [28,85,146,240] 
level_crossings = [55,160,230]
video_path = 'captured_video/data.MOV'
# levels:list = get_the_four_levels(video_path)
max_pulses_per_header = 4
width_guess = 215
crossframe_walk_distance = 140 #guess cause idfk
def threshold_image(levelID):
    if(levelID < 0 or levelID > 3):
        print("Invalid level ID")
        exit()
    if(levelID == 0):
        return (0, level_crossings[0])
    elif(levelID == 1):
        return (level_crossings[0], level_crossings[1])
    elif(levelID == 2):
        return (level_crossings[1], level_crossings[2])
    else:
        return (level_crossings[2], 255)




def header_start_finder(rawframe):
    frame = rawframe
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(2, 2))
    img_clahe = clahe.apply(gray)
    gray = cv2.GaussianBlur(gray, (3, 21), 0)
    _,ret = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    # cv2.imshow('frame',ret) #use this to see what the row detector is seeing when its trying to spot the 255 pulse that indicates header start
    # cv2.waitKey(0)
    header_start_end_pairs = []
    header_start = -1
    width_of_a_pulse = width_guess #approx 230 pixels
    ret =  ret[:,math.floor(ret.shape[1]/2)]
    for j in range(len(ret)):
        if ret[j] == 255:
            if header_start == -1:
                header_start = j
        else:
            if header_start != -1:
                header_end = j
                if (header_end - header_start) >  width_of_a_pulse:
                    header_start_end_pairs.append((header_start, header_end))
                header_start = -1  # reset
    print(header_start_end_pairs) #print this to see what 255 pulses were being caught , the values should be in the high range because you'd want to detect the pulse at the bottom of the frame
    return header_start_end_pairs





def walk_and_get_the_next_pulse(framebuffer,frameid,start_of_walk):
    i = frameid
    total_frames = len(framebuffer)
    while(i < total_frames):
        frame = framebuffer[i]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(2, 2))
        img_clahe = clahe.apply(gray)
        gray = cv2.GaussianBlur(gray, (3, 21), 0)
        if(start_of_walk + width_guess*1.2 >= gray.shape[0]):
            print("Crossframe recovery attempt "+str(i)+"->"+str(i+1))
            i+=1

            start_of_walk -=crossframe_walk_distance
            
            continue
        centerline = gray[:,math.floor(gray.shape[1]/2)]
        centerline = centerline[start_of_walk  : math.floor(start_of_walk + width_guess*1.2)] 
        j = 0
        while(j < len(levels)):
            low, high = threshold_image(j)
            tmp = cv2.inRange(centerline, low, high)       
            header_start = -1
            header_start_end_pairs = []
            closurecheck = False
            for k in range(len(tmp)):
                if tmp[k] == 255:  
                    strikes = 10 
                    closurecheck = True
                    if header_start == -1:
                        header_start = k
                        closurecheck = True
                    
                else:
                    if header_start != -1:
                        header_end = k
                        
                        if (header_end - header_start) >  width_guess/2:
                            header_start_end_pairs.append((header_start, header_end))
                        else:
                            if(strikes > 0):
                                strikes -= 1
                                closurecheck = False
                                continue
                        header_start = -1  # reset
                        closurecheck = False
            if(closurecheck):
                if (len(tmp) - header_start) >  width_guess/2:
                        header_start_end_pairs.append((header_start, len(tmp)))
            if(len(header_start_end_pairs) > 1):
                print("Multiple pulses detected in a single walk, something is wrong")
                print("Frame id :"+str(frameid))
                return -1,-1,-1
            if(len(header_start_end_pairs) == 1):
                return (j,i,header_start_end_pairs[0][1]+start_of_walk) #return the level and the end of the pulse so that we can start walking from there
            j+=1
        break
    return -1,-1,-1
        
        




cap = cv2.VideoCapture(filename=video_path)

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

i = 0
while(i < total_frames):
    frame = frame_buffer[i]
    header_start_end_pairs = header_start_finder(frame)
    if(len(header_start_end_pairs) != 1): #this should ideally be just the start of the header at the bottom of the frame, we can walk for four pulses from this point
        print("Unexpected headers in frame id:"+str(i))
        i+=1
        continue
    #Packet processing start
    
    end_of_header = header_start_end_pairs[0][1]
    if(end_of_header <= frame_buffer[i].shape[0]/2):
        print("Header should be at the bottom of the frame")
        i+=1
        continue
    #walk from here and see what the next level is, do this by threshing the 4 levels.
    
    if(i+1 >= total_frames):
        print("Malformed packet")
        break
        
    frame = frame_buffer[i]
    header_start_end_pairs = header_start_finder(frame)
    end_of_header = header_start_end_pairs[0][1]
    end_of_header += 10 #walk a bit further to avoid the tail of the pulse interfering with the next pulse detection

    j=0
    kys = False
    while(j < max_pulses_per_header):
        symbol,frameID,next_walk = walk_and_get_the_next_pulse(frame_buffer,i,end_of_header)    
        if(symbol == -1):
            kys = True
            break
        print(symbol)

        end_of_header = next_walk+10
        i = frameID
        
        j+=1
    if(kys):
        break
    i+=1
    #Ok so the pulses look like 1 255 (header) , 255, mid like 140, less mid like 60, zero , 255 for header start

    



