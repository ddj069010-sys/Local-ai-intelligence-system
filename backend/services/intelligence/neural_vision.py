import logging
import easyocr
import io

logger = logging.getLogger(__name__)

class NeuralVision:
    """
    Advanced OCR using EasyOCR for reading complex embedded text in images where standard PDF/Tesseract extractors fail.
    Initializes on GPU if available, else falls back to CPU.
    """
    def __init__(self):
        try:
            # We initialize EasyOCR with english. Will use CUDA if available seamlessly.
            self.reader = easyocr.Reader(['en'], gpu=True)
            logger.info("👁️ [NEURAL VISION] EasyOCR Reader initialized successfully.")
        except Exception as e:
            logger.warning(f"⚠️ [NEURAL VISION] EasyOCR init failed (will run without vision): {e}")
            self.reader = None

    def scan_image_bytes(self, image_data: bytes) -> str:
        """Takes raw image bytes, returns extracted text."""
        if not self.reader:
            return ""
            
        try:
            logger.info("👁️ [NEURAL VISION] Processing image byte stream...")
            # detail=0 returns just strings
            results = self.reader.readtext(image_data, detail=0)
            text_extracted = " ".join(results)
            logger.info(f"👁️ [NEURAL VISION] Extracted {len(text_extracted)} characters.")
            return text_extracted
        except Exception as e:
            logger.error(f"❌ [NEURAL VISION] Failed to read image: {e}")
            return ""

neural_vision = NeuralVision()
