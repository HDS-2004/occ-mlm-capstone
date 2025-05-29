import numpy
import cv2 #For image decoding
import os #for file handling
import math
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

img_array_directory = "hw-captures/"
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




def main():
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
        _,ret = cv2.threshold(img_blur,numpy.median(img_blur),255,cv2.THRESH_BINARY)
        ret = cv2.Mat(ret.astype(numpy.uint8))
        # cv2.imshow("w",cv2.resize(ret,(800,600)))
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # return
        os.makedirs("non_header_thresh_results",exist_ok=True)
        output_path = os.path.join('non_header_thresh_results', os.path.basename(img_array[i]))
        cv2.imwrite(output_path, ret)

        vertical_stripe = img_blur[:,math.floor(width/2)] #take all rows from the center of the image. This is the slice we use to demodulate



        actual_data = vertical_stripe.astype(numpy.uint8)
        
        _,actual_data = cv2.threshold(actual_data,0,1,cv2.THRESH_BINARY +cv2.THRESH_OTSU)
        result = actual_data[numpy.insert(actual_data[1:] != actual_data[:-1], 0, True)]
        result = result.astype(numpy.uint8)
        print(result.tobytes().hex(','))
        i+=1
if(__name__ == "__main__"):
    main()