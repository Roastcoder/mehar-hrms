import io

import numpy as np
from PIL import Image, ImageOps


def normalized_image_array(file_obj, size=(32, 32)):
    file_obj.seek(0)
    image = Image.open(file_obj)
    image = ImageOps.exif_transpose(image)
    image = image.convert("L").resize(size)
    array = np.asarray(image, dtype=np.float32)
    file_obj.seek(0)
    return array


def average_hash(array):
    mean = array.mean()
    return array > mean


def compare_images(reference_file, candidate_file):
    reference_array = normalized_image_array(reference_file)
    candidate_array = normalized_image_array(candidate_file)

    reference_hash = average_hash(reference_array)
    candidate_hash = average_hash(candidate_array)

    hash_similarity = 1 - np.not_equal(reference_hash, candidate_hash).mean()
    pixel_delta = np.mean(np.abs(reference_array - candidate_array)) / 255.0
    pixel_similarity = 1 - pixel_delta

    score = round(float((hash_similarity * 0.7) + (pixel_similarity * 0.3)), 4)
    return {
        "score": score,
        "hash_similarity": round(float(hash_similarity), 4),
        "pixel_similarity": round(float(pixel_similarity), 4),
    }
