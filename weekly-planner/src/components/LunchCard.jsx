// components/LunchCard.jsx
import React, { useEffect, useState } from "react";
import { Card } from "./UI";
import { Sandwich } from "lucide-react";
import { authFetch } from "../utils/api"; // <-- updated path
import { toISODate } from "../utils/dates";

export default function LunchCard({ date }) {
  const iso = toISODate(date);
  const [lunch, setLunch] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await authFetch(`/api/lunches?date=${iso}`);
        const todayName = date.toLocaleDateString("en-GB", { weekday: "long" });
        const todayMeal = data?.meals?.find((m) => m.day.toLowerCase() === todayName.toLowerCase());
        setLunch(todayMeal || null);
      } finally {
        setLoading(false);
      }
    })();
  }, [iso, date]);

  return (
    <Card>
      <div className="flex items-center gap-2 mb-2">
        <Sandwich className="w-4 h-4" />
        <h3 className="font-medium">Lunch Today</h3>
      </div>
      {loading ? (
        <div className="text-sm text-zinc-600">Loading…</div>
      ) : lunch ? (
        <div className="text-sm font-medium">{lunch.meal}</div>
      ) : (
        <div className="text-sm text-zinc-500">No lunch planned</div>
      )}
    </Card>
  );
}
