import numpy
import cv2 #For image decoding
import os #for file handling
import math
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

img_array_directory = "sample_packets/"
detection_threshold = 0.5
cammyLowThresh = 30
cammyHighThresh = 100

#Manchester 1 = 0->1
#Manster 0 = 1->0

def find_two_biggest_pairs(input_pairs:tuple)->list[tuple]:
    difference_array = []
    sorted_difference_array = []
    for i in range(len(input_pairs)):
        difference_array.append( abs(input_pairs[i][0] -input_pairs[i][1]))
    sorted_difference_array = sorted(difference_array,reverse=True)
    indexFirst = difference_array.index( sorted_difference_array[0])
    indexSecond = difference_array.index(sorted_difference_array[1])
    return [input_pairs[indexFirst],input_pairs[indexSecond]]

def roughly_equal(a, b, tolerance=0)->bool:
    if a == b:
        return True
    denominator = max(abs(a), abs(b), 1e-12)  # Prevent division by zero
    return abs(a - b) <= tolerance * denominator


def decode_manchester(seq):
    decoded_bits = []
    for i in range(0, len(seq)-1, 2):
        pair = (seq[i], seq[i+1])
        if pair == (1, 0):
            decoded_bits.append(0)
        elif pair == (0, 1):
            decoded_bits.append(1)
    return decoded_bits


def main():
    img_array = []
    for root,dirs,files in os.walk(img_array_directory):
        for file in files:
            if(file.lower().endswith(('.png'))):
                img_array.append(os.path.join(root,file))
    if(len(img_array) != 0):
        print("Found {} images in {} directory".format(len(img_array),img_array_directory))
    else:
        print("No images found!")
        return
    i = 0
    while(i<len(img_array)):
        img = cv2.imread(img_array[i],flags=cv2.IMREAD_GRAYSCALE)
        height,width = img.shape
        vertical_stripe = img[:,math.floor(width/2)] #take all rows from the center of the image. This is the slice we use to demodulate
        clahe = cv2.createCLAHE(clipLimit=2.0,tileGridSize=(2,2))
        vertical_stripe = clahe.apply(vertical_stripe)        
        vertical_stripe_blur = cv2.GaussianBlur(vertical_stripe,(1,21),0) #remove high freq components
        vertical_stripe_normalize = (vertical_stripe_blur - numpy.min(vertical_stripe_blur))/(numpy.max(vertical_stripe_blur)-numpy.min(vertical_stripe_blur))
        # #This removes all high frequency components from the image
        # plt.plot(vertical_stripe_normalize)
        # plt.show()
        # break
       
        
        #Step 1: Edge detection. This makes it easier to identify the header (just find the longest time period without a bit transition)
        clahe = cv2.createCLAHE(clipLimit= 2.0,tileGridSize=(2,2))
        img = clahe.apply(img)
        img_blur = cv2.GaussianBlur(img,(3,21),0)
        med_val = numpy.median(img_blur)
        cammyLowThresh = int(max(0, 0.66 * med_val))
        cammyHighThresh = int(min(255, 1.1 * med_val))
        img_edge = cv2.Canny(img_blur,threshold1=cammyLowThresh,threshold2=cammyHighThresh)
        kernel = numpy.ones((3,3), numpy.uint8)
        img_edge = cv2.morphologyEx(img_edge, cv2.MORPH_CLOSE, kernel)
        vertical_edge_profile = numpy.sum(img_edge,axis=1)
        peaks,_ = find_peaks(vertical_edge_profile,height=0.5*numpy.max(vertical_edge_profile),distance=5) #distance is chosen arbitrarily. No way of knowing
        # plt.plot(vertical_edge_profile) #used to tune
        # plt.plot(peaks, vertical_edge_profile[peaks], "x")
        # plt.title("Vertical Edge Profile with Detected Peaks")
        # plt.show()
        # break
        width_between_peaks = numpy.median(numpy.diff(peaks))
        #Now we know how many bits it takes for a single symbol. Next we find the header to identify the region of interest.
        #Step 2 header identification and subsequent identification of ROI
        binary = (vertical_stripe_normalize>=0.1).astype(numpy.uint8)
        j = 0
        header_start_end_pairs = []
        header_start = -1
        header_end = 0
        while(j<len(binary)):
            if(binary[j] == 0):
                if(header_start == -1):
                    header_start = j
            else:
                if(header_start != -1):
                    header_end = j
                else:
                    j+=1
                    continue
                if((header_end-header_start)>width_between_peaks*2): #adjust this value to capture the header
                    #we got a header of some sort
                    header_start_end_pairs.append((header_start,header_end))
                    header_start = -1
                    header_end = 0
            j+=1
        print(header_start_end_pairs)
        if(len(header_start_end_pairs)<2):
            print("Failed to find a start and end header")
            i+=1
            continue
        elif(len(header_start_end_pairs)>2):
            header_start_end_pairs_biggest= find_two_biggest_pairs(header_start_end_pairs)
            header_start_end_pairs_biggest = sorted(header_start_end_pairs_biggest)
            t_a,t_b = header_start_end_pairs_biggest[0][1],header_start_end_pairs_biggest[1][0]
            if(abs(t_a-t_b)>200):
                #Packet size is usually 170 in the system so this match cant be 
                header_start_end_pairs.remove(header_start_end_pairs_biggest[0])
            else:
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
        #Step 3 extract the binary data
        actual_data = vertical_stripe_normalize[payload_start:payload_end]
        detection_threshold = (max(vertical_stripe_normalize)+min(vertical_stripe_normalize))/2
        actual_data = (actual_data>=detection_threshold).astype(numpy.uint8).flatten()
        diff_mask = numpy.diff(actual_data) != 0
        full_mask = numpy.insert(diff_mask, 0, True) 
        return_data = actual_data[full_mask] #compute the difference between adjancent data points, check whether its not equal to zero (there is a difference), if there is a difference it will mark as true indicating a unique data point, afterwards we add a true to preserve first element. We now use this true/false mask on the original vector to obtain the final data points.
        print(return_data.tobytes().hex(','))
        
        return_data = decode_manchester(return_data[1:])
        print(return_data) #DOESNT WORK, if a zero (0->1) and a one (1->0) was encoded consecutively, [0,1,1,0], it would fail due to duplicate removal creating a unpaired group
        i+=1
if(__name__ == "__main__"):
    main()