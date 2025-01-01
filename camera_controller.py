import cv2
import time
import os
from datetime import datetime

class CameraController:
    def __init__(self, camera_id=0, save_dir='captured_images'):
        self.camera_id = camera_id
        self.save_dir = save_dir
        self.cap = None

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    def initialize_camera(self):
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise Exception("Kamera başlatılamadı!")
        return self.cap.isOpened()

    def capture_image(self):
        if not self.cap or not self.cap.isOpened():
            raise Exception("Kamera başlatılmamış!")

        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Görüntü alınamadı!")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}.jpg"
        filepath = os.path.join(self.save_dir, filename)

        return filepath, frame

    def show_frame(self):
        if not self.cap or not self.cap.isOpened():
            raise Exception("Kamera başlatılmamış!")

        cv2.namedWindow("Kamera Görüntüsü", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Kamera Görüntüsü", 640, 480)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Görüntü akışı kesildi.")
                break

            cv2.imshow('Kamera Görüntüsü', frame)
            if cv2.waitKey(1) == ord('q'):
                break

    def release_camera(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            cv2.destroyAllWindows()
