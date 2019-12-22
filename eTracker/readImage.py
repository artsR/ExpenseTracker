import os
import pytesseract
import cv2
from PIL import Image



FOLDER = os.path.abspath('static\\uploads')

def read_image(im, prep=''):
    """ This function handles the OCR processing image."""

    args = {'image': im, 'preprocess': prep}
    print(FOLDER)
    # Load the image and convert it to grayscale:
    print(os.path.join(FOLDER, args["image"]))
    image = cv2.imread(os.path.join(FOLDER, args["image"]))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Check to see if I should apply thresholding to preprocess the image:
    if args["preprocess"] == "thresh":
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # Make a choice to see if median blurring should be done to remove noise
    elif args["preprocess"] == "blur":
        gray = cv2.medianBlur(gray, 3)

    # Write the preprocessed grayscale image to disc as a temporary file so we can apply OCR to it:
    filename = f"{os.getpid()}.png"
    cv2.imwrite(filename, gray)

    # Load the image as a PIL/Pillow image, apply OCR, and then delete it:
    text = pytesseract.image_to_string(Image.open(filename), lang = "pol")
    os.remove(filename)

    receipt = []
    import re
    rg = re.search(r'(\d+(/|-){1}\d+(/|-){1}\d{2,4})', text)
    print(rg.group())
    for txt in text.split('\n'):
        if txt:
            receipt.append(txt.split())
    from pprint import pprint
    pprint(receipt)
    return text

read_image('receipt_1.jpg')
