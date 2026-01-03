import base64
import io
from typing import Optional, Tuple
import numpy as np
from PIL import Image

class ImageProcessor:
    def __init__(self, target_size: Tuple[int, int] = (28, 28)):
        self.target_size = target_size
    
    def decode_base64(self, base64_data: str) -> Optional[Image.Image]:
        try:
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]
            
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_bytes))
            return image
            
        except Exception as e:
            print(f"Error decoding Base64 image: {e}")
            return None
    
    def preprocess(self, image: Image.Image) -> np.ndarray:
        if image.mode != 'L':
            image = image.convert('L')
        
        image = image.resize(self.target_size, Image.Resampling.LANCZOS)
        
        arr = np.array(image, dtype=np.float32)
        
        arr = arr / 255.0
        
        return arr
    
    def process_canvas_data(self, canvas_data: str) -> Optional[np.ndarray]:
        image = self.decode_base64(canvas_data)
        if image is None:
            return None
        
        return self.preprocess(image)
    
    def process_for_display(self, canvas_data: str, max_size: int = 256) -> Optional[bytes]:
        image = self.decode_base64(canvas_data)
        if image is None:
            return None
        
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

image_processor = ImageProcessor()
