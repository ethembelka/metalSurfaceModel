from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path
import base64
from ultralytics import YOLO
import logging
from crop_object import crop_object_from_original_image
from send_request import post_request

logger = logging.getLogger(__name__)

@dataclass
class Defect:
    defect_type: str
    coordinates: str
    confidence_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "defectType": self.defect_type,
            "coordinates": self.coordinates,
            "confidenceRate": self.confidence_rate
        }

class DefectDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        self.results_folder = Path('results')
        self.results_folder.mkdir(exist_ok=True)

    @staticmethod
    def image_to_base64(image_path: Path) -> str:
        return base64.b64encode(image_path.read_bytes()).decode("utf-8")

    def process_image(self, file_path: str) -> None:
        image_path = Path(file_path)
        original_image_base64 = self.image_to_base64(image_path)
        defective = False
        defects = []

        cropped_path = crop_object_from_original_image(str(image_path))
        if cropped_path is None:
            logger.error(f"No object detected in {image_path.name}")
            return

        results = self.model(str(cropped_path))
        for result in results:
            boxes = result.boxes
            if len(boxes) > 0:
                defective = True
                for box in boxes:
                    defect = Defect(
                        defect_type=result.names[int(box.cls)],
                        coordinates=str(box.xyxy.tolist()[0]),
                        confidence_rate=float(box.conf)
                    )
                    defects.append(defect.to_dict())  # Dict'e çevir

            result_path = self.results_folder / f"result_{image_path.name}"
            result.plot()
            result.save(str(result_path))
            processed_image_base64 = self.image_to_base64(result_path)

            post_request(
                image_path.name,
                original_image_base64,
                processed_image_base64,
                defective,
                defects
            )


detector = DefectDetector('best.pt')

def give_img(file_path: str) -> None:
    try:
        detector.process_image(file_path)
    except Exception as e:
        logger.error(f"Error processing image {file_path}: {e}")