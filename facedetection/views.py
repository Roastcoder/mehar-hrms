from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.http import QueryDict
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models import Company
from facedetection.forms import FaceDetectionSetupForm
from horilla.decorators import hx_request_required

from .serializers import *
from .services import FaceVerificationError, verify_face


class FaceDetectionConfigAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_company(self, request):
        try:
            company = request.user.employee_get.get_company()
            return company
        except Exception as e:
            raise serializers.ValidationError(e)

    def get_facedetection(self, request):
        company = self.get_company(request)
        try:
            facedetection = FaceDetection.objects.get_or_create(company_id=company)
            return facedetection
        except Exception as e:
            raise serializers.ValidationError(e)

    def get(self, request):
        serializer = FaceDetectionSerializer(self.get_facedetection(request)[0])
        return Response(serializer.data, status=status.HTTP_200_OK)

    @method_decorator(
        permission_required("facedetection.add_facedetection", raise_exception=True),
        name="dispatch",
    )
    def post(self, request):
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()
        data["company_id"] = self.get_company(request).id
        serializer = FaceDetectionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_decorator(
        permission_required("facedetection.change_facedetection", raise_exception=True),
        name="dispatch",
    )
    def put(self, request):
        data = request.data
        serializer = FaceDetectionSerializer(
            self.get_facedetection(request)[0], data=data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_decorator(
        permission_required("facedetection.delete_facedetection", raise_exception=True),
        name="dispatch",
    )
    def delete(self, request):
        self.get_facedetection(request).delete()
        return Response(
            {"message": "Facedetection deleted successfully"}, status=status.HTTP_200_OK
        )


class EmployeeFaceDetectionGetPostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _serializer_context(self, request):
        return {"request": request}

    def _delete_stale_record_if_missing_file(self, record):
        if not record or not record.image:
            return record

        try:
            if not record.image.storage.exists(record.image.name):
                record.delete()
                return None
        except Exception:
            # If storage access fails, keep the record untouched.
            return record
        return record

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_company(self, request):
        try:
            company = request.user.employee_get.get_company()
            return company
        except Exception as e:
            raise serializers.ValidationError(e)

    def get_facedetection(self, request):
        company = self.get_company(request)
        try:
            facedetection = FaceDetection.objects.get(company_id=company)
            return facedetection
        except Exception as e:
            raise serializers.ValidationError(e)

    def get_employee_facedetection(self, request):
        """Get the current user's EmployeeFaceDetection record (their face registration)."""
        try:
            employee = request.user.employee_get
            record = EmployeeFaceDetection.objects.get(employee_id=employee)
            return self._delete_stale_record_if_missing_file(record)
        except EmployeeFaceDetection.DoesNotExist:
            return None
        except Exception as e:
            raise serializers.ValidationError(e)

    def get(self, request):
        employee_facedetection = self.get_employee_facedetection(request)
        if employee_facedetection is None:
            return Response(
                {"detail": "No face registration found for this employee."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = EmployeeFaceDetectionSerializer(
            employee_facedetection, context=self._serializer_context(request)
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if self.get_facedetection(request).start:
            employee_id = request.user.employee_get.id
            data = request.data
            if isinstance(data, QueryDict):
                data = data.dict()
            data["employee_id"] = employee_id
            
            # Check if employee already has face detection record
            try:
                existing_record = EmployeeFaceDetection.objects.get(employee_id=employee_id)
                existing_record = self._delete_stale_record_if_missing_file(
                    existing_record
                )
                if existing_record is None:
                    raise EmployeeFaceDetection.DoesNotExist
                # Update existing record
                serializer = EmployeeFaceDetectionSerializer(
                    existing_record,
                    data=data,
                    context=self._serializer_context(request),
                )
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {
                            "success": True,
                            "message": "Face detection image updated successfully",
                            "data": serializer.data
                        }, 
                        status=status.HTTP_200_OK
                    )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except EmployeeFaceDetection.DoesNotExist:
                # Create new record
                serializer = EmployeeFaceDetectionSerializer(
                    data=data, context=self._serializer_context(request)
                )
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {
                            "success": True,
                            "message": "Face detection image uploaded successfully",
                            "data": serializer.data
                        }, 
                        status=status.HTTP_201_CREATED
                    )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        raise serializers.ValidationError("Facedetection not yet started..")


    def put(self, request):
        """Update existing face detection image for the current user."""
        if self.get_facedetection(request).start:
            employee_id = request.user.employee_get.id
            try:
                existing_record = EmployeeFaceDetection.objects.get(employee_id=employee_id)
                existing_record = self._delete_stale_record_if_missing_file(
                    existing_record
                )
                if existing_record is None:
                    raise EmployeeFaceDetection.DoesNotExist
                data = request.data
                if isinstance(data, QueryDict):
                    data = data.dict()
                data["employee_id"] = employee_id
                
                serializer = EmployeeFaceDetectionSerializer(
                    existing_record,
                    data=data,
                    context=self._serializer_context(request),
                )
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {
                            "success": True,
                            "message": "Face detection image updated successfully",
                            "data": serializer.data
                        }, 
                        status=status.HTTP_200_OK
                    )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except EmployeeFaceDetection.DoesNotExist:
                return Response(
                    {"detail": "No face detection record found for this employee."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        raise serializers.ValidationError("Facedetection not yet started..")

    def delete(self, request):
        """Delete face detection record for the current user."""
        employee_id = request.user.employee_get.id
        try:
            existing_record = EmployeeFaceDetection.objects.get(employee_id=employee_id)
            existing_record = self._delete_stale_record_if_missing_file(
                existing_record
            )
            if existing_record is None:
                raise EmployeeFaceDetection.DoesNotExist
            existing_record.delete()
            return Response(
                {"message": "Face detection record deleted successfully"},
                status=status.HTTP_200_OK,
            )
        except EmployeeFaceDetection.DoesNotExist:
            return Response(
                {"detail": "No face detection record found for this employee."},
                status=status.HTTP_404_NOT_FOUND,
            )


class EmployeeFaceDetectionVerifyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    similarity_threshold = float(getattr(settings, "FACE_AUTH_THRESHOLD", 0.82))

    def _delete_stale_record_if_missing_file(self, record):
        if not record or not record.image:
            return record

        try:
            if not record.image.storage.exists(record.image.name):
                record.delete()
                return None
        except Exception:
            return record
        return record

    def _get_face_config(self, request):
        try:
            return FaceDetection.objects.get(company_id=request.user.employee_get.get_company())
        except FaceDetection.DoesNotExist:
            return None

    def post(self, request):
        config = self._get_face_config(request)
        if not config or not config.start:
            return Response(
                {"verified": False, "message": "Face detection is not enabled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            record = EmployeeFaceDetection.objects.get(
                employee_id=request.user.employee_get
            )
        except EmployeeFaceDetection.DoesNotExist:
            return Response(
                {"verified": False, "message": "No enrolled face image found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        record = self._delete_stale_record_if_missing_file(record)
        if record is None:
            return Response(
                {
                    "verified": False,
                    "message": "Stored face image was missing and has been cleared.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        image = request.FILES.get("image")
        if not image:
            return Response(
                {"verified": False, "message": "Capture image is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = verify_face(record.image, image)
        except FaceVerificationError as exc:
            return Response(
                {"verified": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verified = result["verified"]
        response_status = (
            status.HTTP_200_OK if verified else status.HTTP_401_UNAUTHORIZED
        )
        return Response(
            {
                "verified": verified,
                "message": (
                    "Face verification successful."
                    if verified
                    else "Face verification failed."
                ),
                "score": result["score"],
                "threshold": result.get("threshold", self.similarity_threshold),
                "provider": result["provider"],
                "distance": result.get("distance"),
                "model_name": result.get("model_name"),
                "detector_backend": result.get("detector_backend"),
                "hash_similarity": result.get("hash_similarity"),
                "pixel_similarity": result.get("pixel_similarity"),
            },
            status=response_status,
        )


def get_company(request):
    try:
        selected_company = request.session.get("selected_company")
        if selected_company == "all":
            return None
        company = Company.objects.get(id=selected_company)
        return company
    except Exception as e:
        raise serializers.ValidationError(e)


def get_facedetection(request):
    company = get_company(request)
    try:
        location = FaceDetection.objects.get(company_id=company)
        return location
    except Exception as e:
        raise serializers.ValidationError(e)


@login_required
@permission_required("geofencing.add_localbackup")
@hx_request_required
def face_detection_config(request):
    try:
        form = FaceDetectionSetupForm(instance=get_facedetection(request))
    except:
        form = FaceDetectionSetupForm()

    if request.method == "POST":
        try:
            form = FaceDetectionSetupForm(
                request.POST, instance=get_facedetection(request)
            )
        except:
            form = FaceDetectionSetupForm(request.POST)
        if form.is_valid():
            facedetection = form.save(
                commit=False,
            )
            facedetection.company_id = get_company(request)
            facedetection.save()
            messages.success(request, _("facedetection config created successfully."))
        else:
            messages.info(request, "Not valid")
    return render(request, "face_config.html", {"form": form})
