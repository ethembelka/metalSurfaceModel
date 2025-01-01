from dataclasses import dataclass
from datetime import datetime
import threading
import cv2
from pathlib import Path
import logging
from camera_controller import CameraController
from model import give_img
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CameraStatus:
    status: str
    message: str
    timestamp: str
    streaming: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'message': self.message,
            'timestamp': self.timestamp,
            'streaming': self.streaming
        }


class CameraService:
    def __init__(self):
        self._setup_camera()
        self._setup_paths()
        self._setup_state()

    def _setup_camera(self):
        """Kamera kontrolcüsü ve frame kilidi başlatma"""
        self.controller = CameraController()
        self.frame_lock = threading.Lock()
        self.latest_frame: Optional[cv2.Mat] = None

    def _setup_paths(self):
        """Gerekli klasörleri oluşturma"""
        self.input_folder = Path('inputs')
        self.input_folder.mkdir(exist_ok=True)

    def _setup_state(self):
        """Servis durumunu başlatma"""
        self.is_scanning = False
        self.is_streaming = False
        self.scan_thread: Optional[threading.Thread] = None
        self.current_status = CameraStatus(
            status='stopped',
            message='',
            timestamp=datetime.now().isoformat(),
            streaming=False
        )

    def update_status(self, status: str, message: str = '') -> None:
        """Servis durumunu güncelleme"""
        self.current_status = CameraStatus(
            status=status,
            message=message,
            timestamp=datetime.now().isoformat(),
            streaming=self.is_streaming
        )
        logger.info(f"Status updated: {status} - {message}")

    def start_scanning(self) -> bool:
        """Tarama işlemini başlatma"""
        if self.is_scanning:
            logger.warning("Scanning already in progress")
            return False

        try:
            self.is_scanning = True
            self.controller.initialize_camera()
            self.scan_thread = threading.Thread(target=self._capture_loop)
            self.scan_thread.daemon = True  # Ana thread kapanınca bu thread de kapanır
            self.scan_thread.start()
            self.update_status('running', 'Scanning started')
            logger.info("Scanning started, testing image...")
            give_img("test_img.jpg")
            return True
        except Exception as e:
            self.is_scanning = False
            self.update_status('error', str(e))
            logger.error(f"Error starting scan: {e}")
            return False

    def stop_scanning(self) -> bool:
        """Tarama işlemini durdurma"""
        if not self.is_scanning:
            logger.warning("No scanning in progress")
            return False

        try:
            self.is_scanning = False
            self.stop_streaming()
            if self.scan_thread and self.scan_thread.is_alive():
                self.scan_thread.join(timeout=5.0)  # 5 saniye bekle
            self.controller.release_camera()
            self.update_status('stopped', 'Scanning stopped')
            logger.info("Scanning stopped")
            return True
        except Exception as e:
            self.is_scanning = True
            self.update_status('error', str(e))
            logger.error(f"Error stopping scan: {e}")
            return False

    def _capture_loop(self) -> None:
        """Sürekli frame yakalama döngüsü"""
        while self.is_scanning:
            try:
                success, frame = self.controller.capture_image()
                if success:
                    with self.frame_lock:
                        self.latest_frame = frame
                else:
                    logger.warning("Failed to capture frame")
            except Exception as e:
                logger.error(f"Frame capture error: {e}")
                self.update_status('error', str(e))
                break

    def start_streaming(self) -> bool:
        """Stream başlatma"""
        if not self.is_scanning:
            logger.warning("Cannot start streaming: scanning not active")
            return False
        logger.info("Streaming started")
        self.is_streaming = True
        self.current_status.streaming = True
        return True

    def stop_streaming(self) -> bool:
        """Stream durdurma"""
        logger.info("Streaming stopped")
        self.is_streaming = False
        self.current_status.streaming = False
        return True

    def get_frame(self):
        """Stream için frame generator"""
        while self.is_scanning and self.is_streaming:
            with self.frame_lock:
                if self.latest_frame is not None:
                    try:
                        frame = self.latest_frame.copy()
                        success, frame_bytes = cv2.imencode('.jpg', frame)
                        if success:
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes.tobytes() + b'\r\n')
                        else:
                            logger.warning("Failed to encode frame")
                    except Exception as e:
                        logger.error(f"Error in frame generation: {e}")
                        break

    def take_photo(self) -> bool:
        """Fotoğraf çekme"""
        if not self.is_scanning:
            logger.warning("Cannot take photo: scanning not active")
            return False

        with self.frame_lock:
            if self.latest_frame is None:
                logger.warning("No frame available")
                return False

            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = self.input_folder / f"img_{timestamp}.jpg"
                frame = self.latest_frame.copy()
                success, jpeg = cv2.imencode('.jpg', frame)

                if success:
                    file_path.write_bytes(jpeg.tobytes())
                    logger.info(f"Photo saved to: {file_path}")
                    give_img(str(file_path))
                    return True
                else:
                    logger.warning("Failed to encode photo")
                    return False

            except Exception as e:
                logger.error(f"Error saving photo: {e}")
                return False

    def get_status(self) -> Dict[str, Any]:
        """Servis durumunu dict olarak döndürme"""
        return self.current_status.to_dict()