import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load image
file_path = "OOK/sample_packets/frame_663.png"

image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)

if image is None:
    print("Error: Image not found!")
else:
    print("Image loaded successfully!")

# Threshold to find black regions
_, thresh = cv2.threshold(image, 30, 255, cv2.THRESH_BINARY_INV)  # Invert: black -> white

# Sum across rows to find the black headers
row_sums = np.sum(thresh, axis=1)

# Find where the black headers are
black_row_indices = np.where(row_sums > (0.9 * np.max(row_sums)))[0]  # High row sums = big black areas

# Group rows into two regions (header 1 and header 2)
start_row = black_row_indices[-1]  # Bottom black header
end_row = black_row_indices[0]     # Top black header

# Crop the ROI between the headers
roi = image[end_row:start_row, :]

# Threshold the ROI into pure black and white
_, binary_roi = cv2.threshold(roi, 127, 1, cv2.THRESH_BINARY)

# Show result
plt.figure(figsize=(10, 6))
plt.subplot(1, 3, 1)
plt.title('Original')
plt.imshow(image, cmap='gray')

plt.subplot(1, 3, 2)
plt.title('ROI')
plt.imshow(roi, cmap='gray')

plt.subplot(1, 3, 3)
plt.title('Binary ROI (1/0)')
plt.imshow(binary_roi, cmap='gray')
plt.show()
