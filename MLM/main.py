import cv2
from cv2.typing import NumPyArrayNumeric
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
import scipy.stats as stats
from level_identifier import get_the_four_levels
from header_finder import find_header_frames

video_path = 'captured_video/data.MOV'
header_frames:list = find_header_frames(video_path)
levels:list = get_the_four_levels(video_path,header_frames)
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Video error")
    exit()




i = 0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))


while i<len(header_frames):
    cap.set(cv2.CAP_PROP_POS_FRAMES, header_frames[i])
    ret, frame = cap.read()
    
    if not ret:
        print(f"Header error")
        exit()

    # cv2.imshow(f'Header Frame {i} (#{frame_idx})', frame)
    # cv2.waitKey(3000)  # Show each for 500 ms

    # cv2.destroyAllWindows()  # Close each after showing
    #Walk the frames
    currframe = header_frames[i]+1 if header_frames[i]+1<=total_frames else total_frames
    
    endframe = header_frames[i+1] if i + 1 < len(header_frames) else total_frames
    print(f"\nPacket {i}: Frames {currframe} to {endframe}")
    
    for f in range(currframe, endframe):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ret, frame = cap.read()
        f+=1
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ret,frame2 = cap.read()
        f-=1
        if not ret:
            print("Next frame read error")
            exit()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(2, 2))
        frame = clahe.apply(frame)
        frame2 = clahe.apply(frame2)
        frame = cv2.GaussianBlur(frame, (3, 21), 0)
        frame2 = cv2.GaussianBlur(frame2, (3, 21), 0)


        mid01 = levels[0] + (levels[1] - levels[0]) / 2
        mid12 = levels[1] + (levels[2] - levels[1]) / 2
        mid23 = levels[2] + (levels[3] - levels[2]) / 2
        mid01 = np.clip(mid01, levels[0], levels[1])
        mid12 = np.clip(mid12, levels[1], levels[2])
        mid23 = np.clip(mid23, levels[2], levels[3])
        mask0 = cv2.inRange(ret, 0, int(mid01) - 1)                # Level 0
        mask1 = cv2.inRange(ret, int(mid01), int(mid12) - 1)       # Level 1
        mask2 = cv2.inRange(ret, int(mid12), int(mid23) - 1)       # Level 2
        mask3 = cv2.inRange(ret, int(mid23), 255)                  # Level 3
        # Assume frame1 and frame2 are already read via cap.read()
        # Convert to grayscale if they're color
        
        
                    

    i+=1
    


cap.release()

