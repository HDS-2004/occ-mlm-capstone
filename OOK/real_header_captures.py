import numpy
import cv2 #For image decoding
import os #for file handling
import math
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

img_array_directory = "header-hw/"
detection_threshold = 0.5
cammyLowThresh = 30
cammyHighThresh = 100
def find_two_biggest_pairs(input_pairs:tuple)->list[tuple]:
    difference_array = []
    sorted_difference_array = []
    for i in range(len(input_pairs)):
        difference_array.append( abs(input_pairs[i][0] -input_pairs[i][1]))
    sorted_difference_array = sorted(difference_array,reverse=True)
    indexFirst = difference_array.index( sorted_difference_array[0])
    indexSecond = difference_array.index(sorted_difference_array[1])
    return [input_pairs[indexFirst],input_pairs[indexSecond]]

def roughly_equal(a, b, tolerance=0):
    if a == b:
        return True
    denominator = max(abs(a), abs(b), 1e-12)  # Prevent division by zero
    return abs(a - b) <= tolerance * denominator

def find_trailing_zeros_range(arr):
    i = len(arr) - 1
    if arr[i] != 0:
        return None  # No trailing zeros

    end = i
    while i >= 0 and arr[i] == 0:
        i -= 1
    start = i + 1
    length = end - start + 1
    return (start, end, length)

def find_leading_zeros_range(arr):
    i = 0
    if arr[i] != 0:
        return None  # No leading zeros

    start = 0
    while i < len(arr) and arr[i] == 0:
        i += 1
    end = i - 1
    length = end - start + 1
    return (start, end, length)

def main() -> None:
    img_array = []
    for root,dirs,files in os.walk(img_array_directory):
        for file in files:
            if(file.lower().endswith(('.jpg'))):
                img_array.append(os.path.join(root,file))
    if(len(img_array) != 0):
        print("Found {} images in {} directory".format(len(img_array),img_array_directory))
    else:
        print("No images found!")
        return
    i = 0
    while(i<len(img_array)):
        print(img_array[i])
        img = cv2.imread(img_array[i],flags=cv2.IMREAD_GRAYSCALE)
        height,width = img.shape
        

        clahe = cv2.createCLAHE(clipLimit=2.0,tileGridSize=(2,2))
        img = clahe.apply(img)
        img_blur = cv2.GaussianBlur(img,(3,21),0)
        _,ret = cv2.threshold(img_blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        ret = cv2.Mat(ret.astype(numpy.uint8))
        # cv2.imshow("w",cv2.resize(ret,(800,600)))
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # return
        vertical_stripe= img_blur[:,math.floor(width/2)] #take all rows from the center of the image. This is the slice we use to demodulate


        width_between_peaks = 80
        binary = (ret==255).astype(numpy.uint8)[:,math.floor(width/2)] 
        # cv2.imshow("w",cv2.resize(ret,(800,600)))
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # return
        header_start_end_pairs = []
        header_start = -1
        for j in range(len(binary)):
            if binary[j] == 0:
                if header_start == -1:
                    header_start = j
            else:
                if header_start != -1:
                    header_end = j
                    if (header_end - header_start) > width_between_peaks :
                        header_start_end_pairs.append((header_start, header_end))
                    header_start = -1  # reset
        print(header_start_end_pairs)
        if(len(header_start_end_pairs)==1):
            print("Failed to find a start and end header. Attempting fallback")
            first_header_end = header_start_end_pairs[0][1]

            trailing = find_trailing_zeros_range(binary)
            leading = find_leading_zeros_range(binary)

            chosen = None
            if trailing:
                trailing_gap = trailing[0] - first_header_end
            else:
                trailing_gap = -1
            if leading:
                leading_gap = first_header_end - leading[1]
            else:
                leading_gap = -1
            if trailing and (trailing_gap > leading_gap or (trailing_gap == leading_gap and trailing[2] > (leading[2] if leading else 0))):
                chosen = (trailing[0], trailing[1])
            elif leading:
                chosen = (leading[0], leading[1])
            if chosen:
                header_start_end_pairs.append(chosen)
            else:
                print("FAILED TO FIND ANY FALLBACK HEADER!!!.")
                i+=1
                continue
        elif (len(header_start_end_pairs) == 0):
            print("FAILED TO FIND ANY HEADER!!!")
            i+=1
            continue
        elif(len(header_start_end_pairs)>2):
            header_start_end_pairs_biggest= find_two_biggest_pairs(header_start_end_pairs)
            header_start_end_pairs_biggest = sorted(header_start_end_pairs_biggest)
            header_start_end_pairs = header_start_end_pairs_biggest
        # temp_img = cv2.imread(img_array[i],flags=cv2.IMREAD_GRAYSCALE)
        # for header_pair in header_start_end_pairs:
        #     cv2.rectangle(temp_img, (0, header_pair[0]), (img.shape[1], header_pair[1]), (0, 255, 0),-1)
        # cv2.imshow("imds",temp_img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        payload_start = 0
        payload_end = 0
        header_start_end_pairs = sorted(header_start_end_pairs)
        payload_start,payload_end = header_start_end_pairs[0][1],header_start_end_pairs[1][0] #end of the first header , start of the second header
        print("Payload start")
        print(payload_start)
        print("Payload end")
        print(payload_end)
        actual_data = binary[payload_start:payload_end]
        start = -1

        for t in range(len(actual_data)):
            if actual_data[t] == 1:
                if start == -1:
                    start = t
            else:
                if start != -1:
                    if t - start < 160:
                        actual_data[start:t] = 0
                    start = -1

        result = actual_data[numpy.insert(actual_data[1:] != actual_data[:-1], 0, True)]
        result = result.astype(numpy.uint8)
        print(result.tobytes().hex(','))
        i+=1
        
if(__name__ == "__main__"):
    main()