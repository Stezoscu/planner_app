// src/utils/dates.js
import { format, startOfWeek, addDays } from "date-fns";

const TZ = "Europe/London";

export function toISODate(date) {
  return format(date, "yyyy-MM-dd");
}

export function getWeekRange(date) {
  const start = startOfWeek(date, { weekStartsOn: 1 });
  const days = Array.from({ length: 7 }).map((_, i) => addDays(start, i));
  return { start: toISODate(days[0]), end: toISODate(addDays(days[6], 1)), days };
}
