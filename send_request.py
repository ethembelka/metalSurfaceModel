import requests
import json
from datetime import datetime
import base64


url = "http://localhost:8080/api/v1/metal-products/create"

def post_request(name, original_image, processed_image , defective, defects):
    data = {
        "name": name,
        "originalImage": original_image,
        "processedImage": processed_image,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "defective": defective,
        "defectDTOS": defects
    }

    # post istegi
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data), headers=headers)

        if response.status_code == 200:
            print("Başarılı! Yanıt:")
        else:
            print(f"İstek başarısız oldu. Durum kodu: {response.status_code}, Hata: {response.text}")
    except Exception as e:
        print("Hata olustu:", str(e))


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string
'''
image_path = "test_img.jpg"
encoded_image = image_to_base64(image_path)
print(encoded_image)

post_request(
    name="Metal hatasız",
    original_image=encoded_image,
    processed_image=encoded_image,
    defective=False,
    defects=None
)
'''