// Shell.jsx
import React, { useState } from "react";
import { Calendar as CalendarIcon, LogOut } from "lucide-react";
import { Button, Card } from "./components/UI";
import WeekView from "./views/WeekView";
import DayView from "./views/DayView";
import TodaySidebar from "./components/TodaySidebar";
import LunchCard from "./components/LunchCard";
import DinnerCard from "./components/DinnerCard";
import { useAuth } from "./context/AuthContext"; // ✅ fixed path

export default function Shell() {
  const { user, loading, signOutNow } = useAuth();
  const [view, setView] = useState("week"); // 'week' | 'day'
  const [selectedDate, setSelectedDate] = useState(new Date());

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center">
        <div className="text-zinc-600">Loading…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="sticky top-0 bg-white/80 backdrop-blur border-b border-zinc-200 z-40">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CalendarIcon className="w-5 h-5" />
            <span className="font-semibold">Weekly Planner</span>
            <nav className="ml-4 flex items-center gap-2">
              <Button
                className={view === "week" ? "bg-zinc-900 text-white" : ""}
                onClick={() => setView("week")}
              >
                Week
              </Button>
              <Button
                className={view === "day" ? "bg-zinc-900 text-white" : ""}
                onClick={() => setView("day")}
              >
                Day
              </Button>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-zinc-600">{user.displayName}</span>
            {user.photoURL && (
              <img src={user.photoURL} className="w-8 h-8 rounded-full" alt="avatar" />
            )}
            <Button onClick={signOutNow} className="inline-flex items-center gap-2">
              <LogOut className="w-4 h-4" /> Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          {view === "week" ? (
            <WeekView selectedDate={selectedDate} onSelectDate={setSelectedDate} />
          ) : (
            <DayView date={selectedDate} />
          )}
        </div>

        <aside className="lg:col-span-1 space-y-6">
          <TodaySidebar
            date={selectedDate}
            onJumpToToday={() => setSelectedDate(new Date())}
          />
          <LunchCard date={selectedDate} />
          <DinnerCard date={selectedDate} />
        </aside>
      </main>
    </div>
  );
}
