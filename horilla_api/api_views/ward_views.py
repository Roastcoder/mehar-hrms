from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class WardCheckAPIView(APIView):
    """
    Simple API view for ward checking functionality.
    Returns basic ward information for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Check ward information for the current user.
        """
        try:
            user = request.user
            employee = getattr(user, 'employee_get', None)
            
            if not employee:
                return Response({"error": "Employee not found"}, status=404)
            
            # Basic ward check response
            ward_data = {
                "employee_id": employee.id,
                "employee_name": f"{employee.employee_first_name} {employee.employee_last_name}",
                "ward_status": "active",
                "message": "Ward check successful"
            }
            
            return Response(ward_data, status=200)
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)