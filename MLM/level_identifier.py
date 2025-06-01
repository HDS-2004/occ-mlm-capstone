import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
import scipy.stats as stats



def get_the_four_levels(video_path,header_frames):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Invalid file")
        exit()

    histogram = np.zeros(256, dtype=np.int64)
    frame_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if(frame_id in header_frames):
            frame_id+=1
            continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(2, 2))
        img_clahe = clahe.apply(gray)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        

        values, counts = np.unique(gray, return_counts=True)
        histogram[values] += counts
        frame_id+=1

    cap.release()

    intensity_values = []
    for i, count in enumerate(histogram):
        intensity_values.extend([i] * min(count,3000))  # max 500 samples per bin

    X = np.array(intensity_values).reshape(-1, 1)

    gmm = GaussianMixture(n_components=4, random_state=0,init_params='kmeans')
    gmm.fit(X)

    gmm_means = sorted([int(m) for m in gmm.means_.flatten()])
    print(gmm_means)
    #Verify the guesses
    # x = np.linspace(0, 255, 256)
    # plt.hist(intensity_values, bins=256, range=(0,255), density=True, alpha=0.5, color='lightblue')

    # for mean, var, weight in zip(gmm.means_.flatten(), gmm.covariances_.flatten(), gmm.weights_):
    #     gaussian = stats.norm.pdf(x, mean , np.sqrt(var)) * weight
    #     plt.plot(x, gaussian, linewidth=2)

    # plt.title("GMM Gaussians over Histogram")
    # plt.xlabel("Intensity")
    # plt.ylabel("Density")
    # plt.show()

    # # Plot the histogram
    # plt.figure(figsize=(10, 5))
    # plt.bar(range(256), histogram, color='lightblue', edgecolor='black')
    # for mean in gmm_means:
    #     plt.axvline(x=mean, color='crimson', linestyle='--', linewidth=1.5)
    # plt.title("Memory-Safe Intensity Histogram with GMM")
    # plt.xlabel("Pixel Intensity")
    # plt.ylabel("Frequency")
    # plt.show()

    #4 levels found, now iterate from the 0th frame looking for header start.

    # lowest_bic = np.inf
    # best_gmm = None

    # for n in range(2, 7):  # Try 2–6 clusters
    #     gmm = GaussianMixture(n_components=n, random_state=0)
    #     gmm.fit(X)
    #     bic = gmm.bic(X)
    #     if bic < lowest_bic:
    #         lowest_bic = bic
    #         best_gmm = gmm

    # gmm_means = sorted([ best_gmm.means_.flatten()])
    # print(gmm_means)