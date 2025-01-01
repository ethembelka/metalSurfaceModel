import cv2
from pathlib import Path

cropped_folder = Path('cropped')
cropped_folder.mkdir(exist_ok=True)

def crop_object_from_original_image(image_path):

    original_image = cv2.imread(image_path)  # Renkli resim

    gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)

    _, thresholded_image = cv2.threshold(gray_image, 120, 255, cv2.THRESH_TOZERO)

    _, thresh = cv2.threshold(thresholded_image, 1, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)

        x, y, w, h = cv2.boundingRect(largest_contour)

        cropped = original_image[y:y + h, x:x + w]

        cropped_path = cropped_folder / f"cropped_{Path(image_path).name}"
        cv2.imwrite(str(cropped_path), cropped)
        print(f"Kırpılmış görüntü kaydedildi: {cropped_path}")
        return cropped_path  # Kaydedilen dosya yolunu döndür

    print("Kontur bulunamadı.")
    return None
