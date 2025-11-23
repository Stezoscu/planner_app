utils/api.js -> exports authFetch()
context/AuthContext.jsx -> AuthProvider + useAuth()
utils/dates.js -> toISODate(), getWeekRange()
components/TaskEditor.jsx -> new/edit tasks
components/LunchCard.jsx -> lunch UI
components/DinnerCard.jsx -> dinner UI
components/TodaySidebar.jsx -> agenda “Today”
views/WeekView.jsx -> weekly tasks
views/DayView.jsx -> day view (tasks + agenda)
Shell.jsx -> layout + nav
App.jsx -> wires AuthProvider + Shell
