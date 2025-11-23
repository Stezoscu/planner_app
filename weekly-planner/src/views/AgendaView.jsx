// src/views/AgendaView.jsx
import React from "react";

export default function AgendaView({ agenda = [] }) {
  return (
    <ul className="space-y-2">
      {agenda.length === 0 && (
        <li className="text-sm text-zinc-500">Nothing scheduled</li>
      )}
      {agenda.map((a) => (
        <li key={a.id || a.title} className="bg-white rounded-xl border p-3">
          <div className="text-sm font-medium">{a.title}</div>
          <div className="text-xs text-zinc-500">
            {a.time}
            {a.location ? ` • ${a.location}` : ""}
          </div>
          {a.notes && (
            <div className="text-xs text-zinc-500 mt-1">{a.notes}</div>
          )}
        </li>
      ))}
    </ul>
  );
}
