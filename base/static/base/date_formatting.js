class DateFormattingUtility {
    constructor() {
        // Default date format
        this.dateFormat = 'MMM. D, YYYY';
    }

    setDateFormat(format) {
        // Save the selected format to localStorage
        localStorage.setItem('selectedDateFormat', format);
        this.dateFormat = format;
    }

    getFormattedDate(date) {
        if (!date) return '';
        
        // Check if it's already a valid ISO date
        if (moment(date, moment.ISO_8601, true).isValid()) {
            const storedDateFormat = localStorage.getItem('selectedDateFormat') || 'MMM. D, YYYY';
            return moment(date).format(storedDateFormat);
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
            const parsed = moment(date, format, true);
            if (parsed.isValid()) {
                const storedDateFormat = localStorage.getItem('selectedDateFormat') || 'MMM. D, YYYY';
                return parsed.format(storedDateFormat);
            }
        }
        
        // If all else fails, return the original string
        console.warn('Could not parse date:', date);
        return date;
    }


}

// Create an instance of the utility
const dateFormatter = new DateFormattingUtility();

// Retrieve the selected date format from localStorage
const storedDateFormat = localStorage.getItem('selectedDateFormat');

if (storedDateFormat) {
    // If a date format is stored, set it in the utility
    dateFormatter.setDateFormat(storedDateFormat);
}
