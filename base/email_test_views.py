from django.http import JsonResponse
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from datetime import datetime

@method_decorator(csrf_exempt, name='dispatch')
class EmailTestView(View):
    def get(self, request):
        to_email = request.GET.get('to', 'yogendra6378@gmail.com')
        subject = request.GET.get('subject', f'HRMS Email Test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        try:
            message = f"""
HRMS Email Test Successful!

This email confirms your HRMS email system is working correctly.

Test Details:
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- To: {to_email}
- From: Mehar Advisory HRMS

If you received this email, your configuration is working!

---
Mehar Advisory HRMS System
            """
            
            result = send_mail(
                subject=subject,
                message=message,
                from_email='Mehar Advisory <noreply@meharadvisory.cloud>',
                recipient_list=[to_email],
                fail_silently=False
            )
            
            return JsonResponse({
                'status': 'success',
                'message': f'Email sent successfully to {to_email}',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Email failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, status=500)