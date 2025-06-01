import cv2
import numpy as np
import matplotlib.pyplot as plt
def find_header_frames(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Invalid file")
        exit()

    brightness_list = []
    frame_indices = []
    frame_id = 0


    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        
        gray= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        mean_brightness = gray.mean()

        brightness_list.append(mean_brightness)
        frame_indices.append(frame_id)

        frame_id += 1

        #a header occurs when mostly the frame is dark, and theres a low light bar in the middleish, and a strong light bar right after..
        

    cap.release()
    brightness_array = np.array(brightness_list)
    percent = 10
    num_lowest = max(1, int(len(brightness_array) * (percent / 100)))
    sorted_indices = brightness_array.argsort()
    lowest_indices = sorted_indices[:num_lowest]

    # Step 2: Keep only most isolated darkest frames
    proximity_window = 10  # adjust as needed
    final_indices = []

    for idx in lowest_indices:
        frame_num = frame_indices[idx]

        # Skip if this frame is close to any already accepted one
        too_close = any(abs(frame_num - accepted) <= proximity_window for accepted in final_indices)
        if not too_close:
            final_indices.append(frame_num)

    for idx in final_indices:
        print(f"  Frame {idx} with brightness {brightness_array[idx]:.2f}")
    
    #  Optional: plot results
    # plt.figure(figsize=(12, 4))
    # plt.plot(frame_indices, brightness_array, label='Brightness', alpha=0.6)
    # plt.scatter(final_indices,
    #             [brightness_array[i] for i in final_indices],
    #             color='red', label='Selected Dark Frames', zorder=10)
    # plt.title("Frame Brightness Over Time (Filtered)")
    # plt.xlabel("Frame Number")
    # plt.ylabel("Mean Brightness")
    # plt.legend()
    # plt.tight_layout()
    # plt.show()
    return final_indices



