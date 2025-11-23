// src/components/TodaySidebar.jsx
import React, { useEffect, useState } from "react";
import { Card, Button } from "./UI";
import { authFetch } from "../utils/api";
import { toISODate } from "../utils/dates";

export default function TodaySidebar({ date, onJumpToToday }) {
  const iso = toISODate(date);
  const [agenda, setAgenda] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await authFetch(`/api/agenda?date=${iso}`);
        setAgenda(data.items || []);
      } catch (err) {
        console.error("Failed to load today's agenda:", err);
      } finally {
        setLoading(false);
      }
    })();
  }, [iso]);

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-lg">Today</h3>
        <Button
          onClick={onJumpToToday}
          className="bg-zinc-100 hover:bg-zinc-200 text-sm"
        >
          Jump to today
        </Button>
      </div>

      {loading ? (
        <div className="text-sm text-zinc-600">Loading…</div>
      ) : agenda.length === 0 ? (
        <div className="text-sm text-zinc-500">Nothing scheduled</div>
      ) : (
        <ul className="space-y-2">
          {agenda.map((a, idx) => (
            <li
              key={idx}
              className="flex justify-between items-start border rounded-xl bg-white p-2"
            >
              <div className="text-sm font-medium text-zinc-800">{a.title}</div>
              <div className="text-sm text-zinc-700">{a.time || a.value || ""}</div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
