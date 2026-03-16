import tempfile

from django.conf import settings
from PIL import UnidentifiedImageError

from .utils import compare_images


class FaceVerificationError(Exception):
    pass


def _threshold():
    return float(getattr(settings, "FACE_AUTH_THRESHOLD", 0.82))


def _provider():
    return getattr(settings, "FACE_AUTH_PROVIDER", "basic").lower()


def _basic_verify(reference_file, candidate_file):
    result = compare_images(reference_file, candidate_file)
    result["verified"] = result["score"] >= _threshold()
    result["provider"] = "basic"
    result["threshold"] = _threshold()
    return result


def _deepface_verify(reference_file, candidate_file):
    try:
        from deepface import DeepFace
    except ImportError as exc:
        raise FaceVerificationError(
            "DeepFace provider is configured, but the package is not installed."
        ) from exc

    detector_backend = getattr(settings, "FACE_AUTH_DETECTOR_BACKEND", "opencv")
    model_name = getattr(settings, "FACE_AUTH_MODEL_NAME", "ArcFace")

    with tempfile.NamedTemporaryFile(suffix=".jpg") as reference_tmp, tempfile.NamedTemporaryFile(
        suffix=".jpg"
    ) as candidate_tmp:
        reference_file.seek(0)
        candidate_file.seek(0)
        reference_tmp.write(reference_file.read())
        candidate_tmp.write(candidate_file.read())
        reference_tmp.flush()
        candidate_tmp.flush()

        try:
            result = DeepFace.verify(
                img1_path=reference_tmp.name,
                img2_path=candidate_tmp.name,
                model_name=model_name,
                detector_backend=detector_backend,
                enforce_detection=False,
                silent=True,
            )
        except Exception as exc:
            raise FaceVerificationError(str(exc)) from exc
        finally:
            reference_file.seek(0)
            candidate_file.seek(0)

    distance = float(result.get("distance", 1.0))
    threshold = float(result.get("threshold", _threshold()))
    verified = bool(result.get("verified", False))

    return {
        "verified": verified,
        "provider": "deepface",
        "model_name": model_name,
        "detector_backend": detector_backend,
        "score": round(max(0.0, 1.0 - distance), 4),
        "distance": round(distance, 4),
        "threshold": round(threshold, 4),
    }


def verify_face(reference_file, candidate_file):
    try:
        if _provider() == "deepface":
            return _deepface_verify(reference_file, candidate_file)
        return _basic_verify(reference_file, candidate_file)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise FaceVerificationError("Upload a valid image file.") from exc
