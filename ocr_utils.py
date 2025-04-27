import os
from pdf2image import convert_from_path
import pytesseract
import cv2
import numpy as np
from PIL import Image

POPPER_PATH = "./Release-24.08.0-0/poppler-24.08.0/Library/bin"

pytesseract.pytesseract.tesseract_cmd = r"E:/Tesseract/tesseract.exe"


def extract_text_from_pdf(pdf_path: str, dpi: int = 300) -> str:
    """
    把 PDF 每页转成图片，预处理后用 Tesseract OCR，
    最后将所有页的文本拼成一个大字符串返回。
    """
    # 1. 转图片
    images = convert_from_path(pdf_path, dpi=dpi, poppler_path=POPPER_PATH)
    all_text = []

    for page_num, pil_img in enumerate(images, start=1):
        # 2. PIL→OpenCV 数组转换
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        # 3. 灰度
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 4. 自适应二值化
        bin_img = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        # 5. 识别
        custom_config = r"--oem 3 --psm 6"
        text = pytesseract.image_to_string(bin_img, config=custom_config, lang="eng")

        print(f"[Page {page_num}] OCR 识别完成，字符长度：{len(text)}")
        all_text.append(text)

    return "\n".join(all_text)


if __name__ == "__main__":
    pdf_file = "./input_pdf/PaySlip20250403.pdf"
    text = extract_text_from_pdf(pdf_file)
    print(text)
