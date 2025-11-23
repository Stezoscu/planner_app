// src/components/TaskList.jsx
import React from "react";
import { Pencil, Trash2, CheckCircle2, Circle } from "lucide-react";

export default function TaskList({ tasks = [], onEdit, onDelete, onToggle }) {
  if (!tasks?.length) {
    return <div className="text-sm text-zinc-500">No tasks</div>;
  }

  return (
    <ul className="space-y-2">
      {tasks.map((t, index) => (
        <li
          key={`${t.id}-${t.due_date || index}`}  // ✅ ensures uniqueness
          className={`flex items-start gap-2 rounded-xl border p-3 shadow-sm transition hover:shadow-md ${
            t.completed ? "bg-zinc-100/70" : "bg-white"
          }`}
        >
          {/* ✅ Toggle completion icon */}
          <button
            onClick={() => onToggle?.(t)}
            className="mt-0.5 text-zinc-500 hover:text-zinc-800"
            title={t.completed ? "Mark incomplete" : "Mark complete"}
          >
            {t.completed ? (
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            ) : (
              <Circle className="w-5 h-5" />
            )}
          </button>

          {/* ✅ Task content */}
          <div className="flex-1">
            <div
              className={`text-sm font-medium ${
                t.completed ? "line-through text-zinc-400" : "text-zinc-800"
              }`}
            >
              {t.title}
            </div>

            {t.notes && (
              <div className="text-xs text-zinc-500 mt-1">{t.notes}</div>
            )}

            {/* ✅ Show repeat info inline */}
            {t.repeat?.freq && (
              <div className="text-xs text-zinc-400 mt-1 italic">
                Repeats{" "}
                {t.repeat.interval > 1
                  ? `every ${t.repeat.interval} `
                  : "every "}
                {t.repeat.freq}
                {t.repeat.until &&
                  ` until ${new Date(t.repeat.until).toLocaleDateString()}`}
              </div>
            )}
          </div>

          {/* ✅ Action buttons */}
          <div className="flex items-center gap-1 ml-2">
            <button
              onClick={() => onEdit?.(t)}
              className="text-zinc-500 hover:text-zinc-800"
              title="Edit task"
            >
              <Pencil className="w-4 h-4" />
            </button>
            <button
              onClick={() => onDelete?.(t)}
              className="text-zinc-500 hover:text-red-600"
              title="Delete task"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
