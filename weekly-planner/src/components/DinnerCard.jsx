// components/DinnerCard.jsx
import React, { useEffect, useState } from "react";
import { Card } from "./UI";
import { ChefHat } from "lucide-react";
import { authFetch } from "../utils/api"; // <-- updated path
import { toISODate } from "../utils/dates";

export default function DinnerCard({ date }) {
  const iso = toISODate(date);
  const [dinner, setDinner] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await authFetch(`/api/dinner?date=${iso}`);
        const todayName = date.toLocaleDateString("en-GB", { weekday: "long" });
        const todayMeal = data?.meals?.find(
          (m) => m.day.toLowerCase() === todayName.toLowerCase()
        );
        setDinner(todayMeal || null);
      } finally {
        setLoading(false);
      }
    })();
  }, [iso, date]); // <-- added date for completeness

  return (
    <Card>
      <div className="flex items-center gap-2 mb-2">
        <ChefHat className="w-4 h-4" />
        <h3 className="font-medium">Dinner Tonight</h3>
      </div>
      {loading ? (
        <div className="text-sm text-zinc-600">Loading…</div>
      ) : dinner ? (
        <div className="text-sm font-medium">{dinner.meal}</div>
      ) : (
        <div className="text-sm text-zinc-500">No dinner planned</div>
      )}
    </Card>
  );
}
