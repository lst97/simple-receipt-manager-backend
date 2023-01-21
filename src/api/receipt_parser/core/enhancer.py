# !/usr/bin/python3
# coding: utf-8

# Copyright 2015-2018
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

import cv2
import numpy as np
from PIL import Image
from pytesseract import pytesseract
from wand.image import Image as WandImage
from scipy.ndimage import interpolation as inter
from os.path import join, dirname
import logging
import coloredlogs
import imagehash

from .receipt import Receipt
from .config import read_config, read_image_hashs, write_image_hashs

IMAGE_FOLDER = "data/img"
TMP_FOLDER = "data/tmp"
TEXT_FOLDER = "data/txt"

BASE_PATH = dirname(dirname(__file__))
INPUT_FOLDER = os.path.join(BASE_PATH, IMAGE_FOLDER)
OUTPUT_TMP_FOLDER = os.path.join(BASE_PATH, TMP_FOLDER)
OUTPUT_FOLDER = os.path.join(BASE_PATH, TEXT_FOLDER)

CONFIG_YML_PATH = 'config/config.yml'
CONFIG_HASHS_PATH = 'config/.hashs.json'

ORANGE = '\033[33m'
RESET = '\033[0m'

LOGGER = logging.getLogger("parser_core.enhancer")


def prepare_folders():
    """
    :return: void
        Creates necessary folders
    """

    for folder in [
        INPUT_FOLDER, OUTPUT_TMP_FOLDER, OUTPUT_FOLDER
    ]:
        if not os.path.exists(folder):
            os.makedirs(folder)


def find_images(folder):
    """
    :param folder: str
        Path to folder to search
    :return: generator of str
        List of images in folder
    """

    for file in os.listdir(folder):
        full_path = os.path.join(folder, file)
        if os.path.isfile(full_path):
            try:
                _ = Image.open(full_path)  # if constructor succeeds
                yield file
            except:
                pass


def rotate_image(input_file, output_file, angle=90):
    """
    :param input_file: str
        Path to image to rotate
    :param output_file: str
        Path to output image
    :param angle: float
        Angle to rotate
    :return: void
        Rotates image and saves result
    """
    with WandImage(filename=input_file) as img:
        width, height = img.size
        if width < height:
            angle = 0

        print(ORANGE + '\t~: ' + RESET +
              'Rotate image by: ' + str(angle) + "°" + RESET)
        with img.clone() as rotated:
            rotated.rotate(angle)
            rotated.save(filename=output_file)


def deskew_image(image, delta=1, limit=5):
    """
    Rotate image to correct skew angle
    :param image: numpy.ndarray
        Image to be deskewed
    :param delta: int
        Increment of angle to check in each iteration
    :param limit: int
        Maximum angle to check for skew
    :return: numpy.ndarray
        Deskewed image
    """
    # Helper function to calculate score of image at a certain angle
    def determine_score(arr, angle):
        data = inter.rotate(arr, angle, reshape=False, order=0)
        histogram = np.sum(data, axis=1)
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2)
        return histogram, score

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply Otsu thresholding to binarize the image
    thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    scores = []
    # Try rotating the image by different angles in the range (-limit, limit+delta)
    angles = np.arange(-limit, limit + delta, delta)
    for angle in angles:
        histogram, score = determine_score(thresh, angle)
        scores.append(score)

    # Get the angle that resulted in the highest score
    best_angle = angles[scores.index(max(scores))]

    (h, w) = image.shape[:2]
    # Get the center of the image
    center = (w // 2, h // 2)
    # Get the rotation matrix for rotating the image by the best angle
    M = cv2.getRotationMatrix2D(center, best_angle, 1.0)

    print(f"Deskew image by: {best_angle} angle")

    # Rotate the image using the rotation matrix
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated


def run_tesseract(input_file, output_file, language="eng"):
    """
    :param input_file: str
        Path to image to OCR
    :param output_file: str
        Path to output file
    :return: void
        Runs tesseract on image and saves result
    """

    print(ORANGE + '\t~: ' + RESET + 'Parse image using pytesseract' + RESET)
    print(ORANGE + '\t~: ' + RESET + 'Parse image at: ' + input_file + RESET)
    print(ORANGE + '\t~: ' + RESET + 'Write result to: ' + output_file + RESET)

    # Open the input file as a binary stream
    with open(input_file, 'rb') as f:
        # Use WandImage to open the file as an image
        with WandImage(file=f) as img:
            # Use pytesseract to perform OCR on the image
            image_data = pytesseract.image_to_string(
                img, lang=language)
            # Open the output file in write mode and write the OCR text to it
            with open(output_file, 'w', encoding='utf-8') as output:
                output.write(image_data)
    print("OCR text written to: ", output_file)


def rescale_image(img):
    print(ORANGE + '\t~: ' + RESET + 'Rescale image' + RESET)
    img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
    return img


def grayscale_image(img):
    print(ORANGE + '\t~: ' + RESET + 'Grayscale image' + RESET)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def remove_noise(img):
    # Apply morphological operations to remove noise from the image
    kernel = np.ones((1, 1), np.uint8)
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)

    print(ORANGE + '\t~: ' + RESET +
          'Applying gaussianBlur and medianBlur' + RESET)

    # Apply Gaussian and median blur to smooth the image
    img = cv2.GaussianBlur(img, (5, 5), 0)
    img = cv2.medianBlur(img, 5)

    # removed cv2.bilateralFilter() as it is not necessary in this case and it increase the complexity and time consumed.

    # Apply adaptive thresholding to binarize the image
    img = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)

    return img


def remove_shadows(img):
    """
    Remove shadows from the image by subtracting the background from the image
    :param img: numpy array, the image to process
    :return: numpy array, the processed image
    """
    # Split the image into its RGB planes
    rgb_planes = cv2.split(img)

    # Initialize the result planes and result norm planes lists
    result_planes = []
    result_norm_planes = []

    # Iterate over each plane
    for plane in rgb_planes:
        # Dilate the plane to remove small dark spots
        dilated_img = cv2.dilate(plane, np.ones((7, 7), np.uint8))

        # Use median blur to smooth the image
        bg_img = cv2.medianBlur(dilated_img, 21)

        # Subtract the background from the image
        diff_img = 255 - cv2.absdiff(plane, bg_img)

        # Normalize the image to the range of 0-255
        norm_img = cv2.normalize(
            diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)

        # Append the processed image to the result planes and result norm planes lists
        result_planes.append(diff_img)
        result_norm_planes.append(norm_img)

    # Merge the processed planes into a single image
    result = cv2.merge(result_planes)

    return result


def detect_orientation(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    print(ORANGE + '\t~: ' + RESET + 'Get rotation angle:' + str(angle) + RESET)

    return image


def enhance_image(img, tmp_path, high_contrast=True, gaussian_blur=True, rotate=True):
    img = rescale_image(img)

    if rotate:
        cv2.imwrite(tmp_path, img)
        rotate_image(tmp_path, tmp_path)
        img = cv2.imread(tmp_path)

    img = deskew_image(img)
    img = remove_shadows(img)

    if high_contrast:
        img = grayscale_image(img)

    if gaussian_blur:
        img = remove_noise(img)

    return img


def process_receipt(config, filename, rotate=True, grayscale=True, gaussian_blur=True):
    input_path = INPUT_FOLDER + "/" + filename

    output_path = OUTPUT_FOLDER + "/" + filename.split(".")[0] + ".txt"

    LOGGER.info(ORANGE + '~: ' + RESET + 'Process image: ' +
                ORANGE + input_path + RESET)
    prepare_folders()

    try:
        img = cv2.imread(input_path)
    except FileNotFoundError:
        return Receipt(config=config, raw="")

    tmp_path = os.path.join(
        OUTPUT_TMP_FOLDER, filename
    )
    img = enhance_image(img, tmp_path, grayscale, gaussian_blur)

    LOGGER.info(ORANGE + '~: ' + RESET + 'Temporary store image at: ' +
                ORANGE + tmp_path + RESET)

    cv2.imwrite(tmp_path, img)
    run_tesseract(tmp_path, output_path, config.language)

    LOGGER.info(ORANGE + '~: ' + RESET + 'Store parsed text at: ' +
                ORANGE + output_path + RESET)
    raw = open(output_path, 'r').readlines()

    return Receipt(config=config, raw=raw)


def check_hash(img_path, hash_str, img_hashs):
    for item in img_hashs["records"]:
        if item['hash'] == hash_str:
            LOGGER.info(img_path + " already enhanced.")
            LOGGER.info("Process next image. (SKIP)")
            return True
    return False


def run():
    coloredlogs.install(level='DEBUG')
    coloredlogs.install(level='DEBUG', logger=LOGGER)

    prepare_folders()

    config = read_config(config=join(
        dirname(dirname(__file__)), CONFIG_YML_PATH))

    img_hashs = read_image_hashs(config=join(
        dirname(dirname(__file__)), CONFIG_HASHS_PATH))

    images = list(find_images(INPUT_FOLDER))
    LOGGER.info(ORANGE + '~: ' + RESET + 'Found: ' + ORANGE + str(len(images)
                                                                  ) + RESET + ' images in: ' + ORANGE + IMAGE_FOLDER + RESET)

    i = 1
    for image in images:
        input_path = os.path.join(
            INPUT_FOLDER,
            image
        )
        tmp_path = os.path.join(
            OUTPUT_TMP_FOLDER,
            image
        )

        out_path = os.path.join(
            OUTPUT_FOLDER,
            image + ".txt"
        )

        if i != 1:
            print()

        LOGGER.info("Start imagehash for compararson")
        img_hash_str = str(imagehash.average_hash(Image.open(input_path)))
        if check_hash(image, img_hash_str, img_hashs) == True:
            i = i + 1
            continue
        LOGGER.info("Hash not found.")

        LOGGER.info(ORANGE + '~: ' + RESET + 'Process image (' + ORANGE + str(i) + '/' + str(
            len(images)) + RESET + ') : ' + input_path.split('/')[-1] + RESET)

        img = cv2.imread(input_path)
        img = enhance_image(img, tmp_path)
        cv2.imwrite(tmp_path, img)

        run_tesseract(tmp_path, out_path, config.language)

        write_image_hashs(image, img_hash_str, img_hashs, config=join(
            dirname(dirname(__file__)), CONFIG_HASHS_PATH))
        i = i + 1

    LOGGER.info("Enhancer exit.")