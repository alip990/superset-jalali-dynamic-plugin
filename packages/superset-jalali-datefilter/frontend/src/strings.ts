/** Persian UI copy. Yeh/keh are Persian (ی/ک), and ZWNJ is used where required. */

export const STR = {
  noFilter: 'بدون فیلتر',
  presets: 'بازه‌های آماده',
  custom: 'بازه دلخواه',
  advanced: 'پیشرفته',
  apply: 'اعمال',
  cancel: 'انصراف',
  from: 'از',
  to: 'تا',
  today: 'امروز',
  yesterday: 'دیروز',
  last7: '۷ روز اخیر',
  last30: '۳۰ روز اخیر',
  last90: '۹۰ روز اخیر',
  thisWeek: 'این هفته',
  thisMonth: 'این ماه',
  lastMonth: 'ماه گذشته',
  thisSeason: 'این فصل',
  lastSeason: 'فصل گذشته',
  thisYear: 'امسال',
  lastYear: 'سال گذشته',
  prevMonth: 'ماه قبل',
  nextMonth: 'ماه بعد',
  errorInvalid: 'تاریخ نامعتبر است',
  errorOrder: 'تاریخ پایان نباید پیش از شروع باشد',
  errorRange: 'تاریخ خارج از بازه پشتیبانی‌شده است',
  hintRolling:
    'برای مقدار پیش‌فرض، بازه‌های متحرک مثل «امروز» یا «۷ روز اخیر» را بگذارید. ماه و سال شمسی به\u200cصورت تاریخ ثابت ذخیره می‌شوند.',
  advancedLabel: 'عبارت زمانی سوپرست',
  triggerLabel: 'بازه تاریخ',
};

export const MONTHS = [
  'فروردین',
  'اردیبهشت',
  'خرداد',
  'تیر',
  'مرداد',
  'شهریور',
  'مهر',
  'آبان',
  'آذر',
  'دی',
  'بهمن',
  'اسفند',
] as const;

export const WEEKDAY_INITIALS = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'] as const;
