// Simple date utility functions to replace date-fns for this demo
export const format = (date: Date, formatStr: string): string => {
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];
  
  const fullMonths = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const day = date.getDate();
  const month = date.getMonth();
  const year = date.getFullYear();
  const hours = date.getHours();
  const minutes = date.getMinutes();

  switch (formatStr) {
    case 'MMM dd, yyyy':
      return `${months[month]} ${day.toString().padStart(2, '0')}, ${year}`;
    case 'MMMM dd, yyyy':
      return `${fullMonths[month]} ${day.toString().padStart(2, '0')}, ${year}`;
    case 'MMM dd':
      return `${months[month]} ${day.toString().padStart(2, '0')}`;
    case 'MMMM dd, yyyy h:mm a':
      const ampm = hours >= 12 ? 'PM' : 'AM';
      const hour12 = hours % 12 || 12;
      return `${fullMonths[month]} ${day.toString().padStart(2, '0')}, ${year} ${hour12}:${minutes.toString().padStart(2, '0')} ${ampm}`;
    default:
      return date.toLocaleDateString();
  }
};

export const startOfWeek = (date: Date): Date => {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day;
  return new Date(d.setDate(diff));
};

export const endOfWeek = (date: Date): Date => {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + 6;
  return new Date(d.setDate(diff));
};

export const subWeeks = (date: Date, weeks: number): Date => {
  const d = new Date(date);
  d.setDate(d.getDate() - (weeks * 7));
  return d;
};

export const eachWeekOfInterval = (interval: { start: Date; end: Date }): Date[] => {
  const weeks: Date[] = [];
  const current = new Date(interval.start);
  
  while (current <= interval.end) {
    weeks.push(new Date(current));
    current.setDate(current.getDate() + 7);
  }
  
  return weeks;
};