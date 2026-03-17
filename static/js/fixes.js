// Missing reloadMessage function
function reloadMessage() {
    location.reload();
}

// Improved date formatting utility to fix moment.js deprecation warnings
function formatDateSafely(dateString) {
    if (!dateString) return '';
    
    // Check if it's already a valid ISO date
    if (moment(dateString, moment.ISO_8601, true).isValid()) {
        return moment(dateString).format(localStorage.getItem('selectedDateFormat') || 'MMM. D, YYYY');
    }
    
    // Try to parse common date formats
    const formats = [
        'YYYY-MM-DD',
        'MM/DD/YYYY',
        'DD/MM/YYYY',
        'DD-MM-YYYY',
        'DD.MM.YYYY',
        'MMMM D, YYYY',
        'MMM D, YYYY'
    ];
    
    for (let format of formats) {
        const parsed = moment(dateString, format, true);
        if (parsed.isValid()) {
            return parsed.format(localStorage.getItem('selectedDateFormat') || 'MMM. D, YYYY');
        }
    }
    
    // If all else fails, return the original string
    console.warn('Could not parse date:', dateString);
    return dateString;
}

// Override the original getFormattedDate function to use safer parsing
if (typeof dateFormatter !== 'undefined' && dateFormatter.getFormattedDate) {
    dateFormatter.getFormattedDate = function(date) {
        return formatDateSafely(date);
    };
}

// Global error handler for moment.js deprecation warnings
if (typeof moment !== 'undefined') {
    moment.suppressDeprecationWarnings = true;
}