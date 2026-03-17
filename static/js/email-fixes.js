// Email-specific JavaScript fixes
$(document).ready(function() {
    // Override the loadTemplate function to handle errors better
    window.loadTemplate = function(select) {
        const id = $(select).val();
        if (!id) return;
        
        $.ajax({
            type: "get",
            url: `/employee/get-template/${id}/`,
            dataType: "json",
            beforeSend: function() { 
                if ($('#writeField').length && $('#writeField').summernote) {
                    $('#writeField').summernote('disable'); 
                }
            },
            success: function(response) { 
                if ($('#writeField').length && $('#writeField').summernote) {
                    $('#writeField').summernote('code', response.body || ''); 
                }
            },
            error: function(xhr, status, error) {
                console.error('Template loading error:', error);
                Swal.fire({
                    title: 'Template Error',
                    text: 'Failed to load email template. Please try again.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            },
            complete: function() { 
                if ($('#writeField').length && $('#writeField').summernote) {
                    $('#writeField').summernote('enable'); 
                }
            }
        });
    };
    
    // Handle form submission errors for email forms
    $(document).on('htmx:responseError', function(event) {
        if (event.detail.pathInfo.requestPath.includes('send-mail')) {
            console.error('Email sending error:', event.detail);
            Swal.fire({
                title: 'Email Error',
                text: 'Failed to send email. Please check your email configuration and try again.',
                icon: 'error',
                confirmButtonText: 'OK'
            });
        }
    });
    
    // Prevent date formatting errors in email templates
    window.safeDateFormat = function(dateValue) {
        if (!dateValue || dateValue === 'None' || dateValue === null || dateValue === undefined) {
            return '';
        }
        
        try {
            if (typeof dateFormatter !== 'undefined' && dateFormatter.getFormattedDate) {
                return dateFormatter.getFormattedDate(dateValue);
            }
            return dateValue;
        } catch (error) {
            console.warn('Date formatting error:', error);
            return dateValue || '';
        }
    };
});

// Global error handler for email-related JavaScript errors
window.addEventListener('error', function(event) {
    if (event.message.includes('reloadMessage') || 
        event.message.includes('moment') || 
        event.message.includes('date')) {
        console.warn('Handled email-related error:', event.message);
        event.preventDefault();
        return true;
    }
});