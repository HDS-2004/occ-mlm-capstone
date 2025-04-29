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

#TODO: Clarify whether we need to read the second image to deciper a full packet
#TODO: Clarify on a method to avoid the weird bloom effects in high light regions and the reverse effect in dark regions

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


class DecoderSpecification:
    def __init__(self,zerobit_threshold,onebit_threshold,zerorows_per_bit_threshold, onerows_per_bit_threshold):
        self.zerobit_threshold = zerobit_threshold
        self.onebit_threshold = onebit_threshold
        self.zerorows_per_bit_threshold = zerorows_per_bit_threshold
        self.onerows_per_bit_threshold = onerows_per_bit_threshold

'''
Returns a list, the list contains a list which contains the following data
The list is sorted such that start_row is the lowest to highest (top bottom)

[[start_row,DecoderSpecification]]
If width_between_peaks is not 0, its calculated using camera_exposure_time(sec) and led_max_rate(hz). Otherwise those parameters are ignored
'''
def dynamic_clock_recovery(image_processed: cv2.Mat,header_start_end_pair:tuple,width_between_peaks:int, camera_exposure_time=0.1,led_max_rate=1000) -> list[list]:
    height,width = image_processed.shape
    if(width_between_peaks == 0):
        width_between_peaks= width/camera_exposure_time*led_max_rate
    start_payload = header_start_end_pair[0]
    end_payload = header_start_end_pair[1]
    #strip everything except the payload data
    image_processed = image_processed[start_payload:end_payload,:]
    image_normalized= (image_processed - numpy.min(image_processed))/(numpy.max(image_processed)-numpy.min(image_processed))

    
    scan_region = int(width_between_peaks*3)
    threshed_image = (image_normalized>=0.5).astype(numpy.uint8)
    #scan and get parameters
    scan_cycles= math.floor(image_normalized.shape[1]/scan_region)
    theList = []
    for i in range(0,scan_cycles):
        onerows_per_bit_threshold = 0
        zerorows_per_bit_threshold = 0
        recorded_zero_intensities = []
        recorded_one_intensities = []
        scan_img_region = image_normalized[i*scan_region:i*scan_region+scan_region,:]
        thresh_scan_img_region = threshed_image[i*scan_region:i*scan_region+scan_region,:]
        for j,value in enumerate(scan_img_region[:,width//2]):
            if(thresh_scan_img_region[j][width//2] == 0):
                recorded_zero_intensities.append(value)
            else:
                recorded_one_intensities.append(value)
        
        for j,value in enumerate(scan_img_region[:,width//2 + 5]):
            if(thresh_scan_img_region[j][width//2+5] == 0):
                recorded_zero_intensities.append(value)
            else:
                recorded_one_intensities.append(value)
        
        for j,value in enumerate(scan_img_region[:,width//2-5] ):
            if(thresh_scan_img_region[j][width//2-5] == 0):
                recorded_zero_intensities.append(value)
            else:
                recorded_one_intensities.append(value)
        median_intensity_one_bit = numpy.mean(recorded_one_intensities) if recorded_one_intensities else 0.5
        median_intensity_zero_bit = numpy.mean(recorded_zero_intensities) if recorded_zero_intensities  else 0.5
        new_scan_img_region = (scan_img_region>=median_intensity_one_bit).astype(numpy.uint8)
        new_scan_img_region2 = (scan_img_region>=median_intensity_zero_bit).astype(numpy.uint8)

        runner_counters_ones= []
        runner_counters_zeros = []
        if(median_intensity_one_bit !=0):
            runner_counter = 0
            for j in range(len(scan_img_region[:,width//2])):
                if(new_scan_img_region[j][width//2] == 1):
                    runner_counter+=1
                elif runner_counter != 0:
                    runner_counters_ones.append(runner_counter)
                    runner_counter = 0
            onerows_per_bit_threshold = numpy.median(runner_counters_ones)
        if(len(recorded_zero_intensities) !=0):
            runner_counter = 0
            for j in range(len(scan_img_region[:,width//2])):
                if(new_scan_img_region2[j][width//2] == 0):
                    runner_counter+=1
                elif runner_counter != 1:
                    runner_counters_zeros.append(runner_counter)
                    runner_counter = 0
            zerorows_per_bit_threshold = numpy.median(runner_counters_zeros)
        obj = DecoderSpecification(median_intensity_zero_bit,median_intensity_one_bit,zerorows_per_bit_threshold,onerows_per_bit_threshold)
        theList.append([start_payload+i*scan_region,min(start_payload+i*scan_region+scan_region,end_payload),obj])
    return theList




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
        img = cv2.imread(img_array[i],flags=cv2.IMREAD_GRAYSCALE)
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
                header_start_end_pairs = header_start_end_pairs[0]
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
        actual_data = (actual_data>=detection_threshold).astype(numpy.uint8)
        cleaned_actual_data = []
        # runner_counter = 0
        # for r in range(len(actual_data)):
        #     #TODO This needs to be patched such that: 
        #     #When the relative difference between a light region and dark region is lower, the signal must increase the threshold value for dark regions and decrease it for light regions. 
        #     #Rn its hardcoded so it doesnt work properly
        #     if(r == len(actual_data)-1):
        #         continue
        #     if(actual_data[r] == actual_data[r+1]):
        #         runner_counter+=1
        #         if(actual_data[r] == 1 and roughly_equal(runner_counter,7,0)):
        #             cleaned_actual_data.append(actual_data[r])
        #             runner_counter = 0
        #         elif (actual_data[r] == 0 and roughly_equal(runner_counter,3,0)):
        #             cleaned_actual_data.append(actual_data[r])
        #             runner_counter = 0
        #         # elif(actual_data[r] == 1):
        #         #     print("ones "+str(runner_counter))
        #         # elif(actual_data[r] == 0):
        #         #     print("zeroes "+ str(runner_counter))
        #     else:
        #         runner_counter = 1
        # # ascii_string = actual_data.tobytes().decode('ascii')
        # # print(ascii_string)
        # cleaned_actual_data = numpy.array(cleaned_actual_data,dtype=numpy.uint8)
        # print(cleaned_actual_data.tobytes().hex(','))
        img = cv2.imread(img_array[i],flags=cv2.IMREAD_GRAYSCALE)
        height,width = img.shape
        clahe = cv2.createCLAHE(clipLimit=2.0,tileGridSize=(2,2))
        img = clahe.apply(img) 
        
        img = cv2.GaussianBlur(img,(1,3),0.5) 
        theList = dynamic_clock_recovery(img,(payload_start,payload_end),width_between_peaks)
        vertical_stripe = img[:,math.floor(width/2)] #take all rows from the center of the image. This is the slice we use to demodulate    
        vertical_stripe_normalize = (vertical_stripe - numpy.min(vertical_stripe))/(numpy.max(vertical_stripe)-numpy.min(vertical_stripe))

        for l,retList in enumerate(theList):
            one_bit_thresh = retList[2].onebit_threshold
            zero_bit_thresh = retList[2].zerobit_threshold
            zerorows_per_bit_threshold = retList[2].zerorows_per_bit_threshold
            onerows_per_bit_threshold = retList[2].onerows_per_bit_threshold
            actual_data = (vertical_stripe_normalize>=one_bit_thresh).astype(numpy.uint8)
            actual_data2 = (vertical_stripe_normalize>=zero_bit_thresh).astype(numpy.uint8)
            runner_counter = 0
            for r in range(retList[0],retList[1]):
                #TODO This needs to be patched such that: 
                #When the relative difference between a light region and dark region is lower, the signal must increase the threshold value for dark regions and decrease it for light regions. 
                #Rn its hardcoded so it doesnt work properly
                if(r == len(actual_data)-1):
                    continue
                if(actual_data[r] == actual_data[r+1] and actual_data[r] == 1):
                    runner_counter+=1
                    if(actual_data[r] == 1 and runner_counter == onerows_per_bit_threshold):
                        cleaned_actual_data.append(1)
                        runner_counter = 0
                else:
                    runner_counter = 0
            for r in range(retList[0],retList[1]):
                #TODO This needs to be patched such that: 
                #When the relative difference between a light region and dark region is lower, the signal must increase the threshold value for dark regions and decrease it for light regions. 
                #Rn its hardcoded so it doesnt work properly
                if(r == len(actual_data)-1):
                    continue
                if(actual_data[r] == actual_data[r+1] and actual_data[r] == 0):
                    runner_counter+=1
                    if(actual_data[r] == 0 and runner_counter == zerorows_per_bit_threshold):
                        cleaned_actual_data.append(0)
                        runner_counter = 0
                else:
                    runner_counter = 0
        print(cleaned_actual_data)
        return
        i+=1
if(__name__ == "__main__"):
    main()