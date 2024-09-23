export function formatDate(dateString: string) {
    const date = new Date(dateString);
    
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June', 
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    
    const month = months[date.getUTCMonth()];
    const day = date.getUTCDate();
    const year = date.getUTCFullYear();
    
    // Function to add ordinal suffix to day
    function getOrdinalSuffix(day: number) {
        if (day > 3 && day < 21) return 'th';
        switch (day % 10) {
            case 1:  return "st";
            case 2:  return "nd";
            case 3:  return "rd";
            default: return "th";
        }
    }
    
    return `${month} ${day}${getOrdinalSuffix(day)}, ${year}`;
}