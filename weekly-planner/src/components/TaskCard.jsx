import React from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Pencil, Trash2, CheckCircle2, Circle } from "lucide-react";

export default function TaskCard({ task, onEdit, onDelete, onToggle }) {
  // Unique per *occurrence* (your backend expands recurring tasks into dates)
  const occId = `${task.id}-${(task.due_date || "").slice(0, 10)}`;

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: occId, data: { task } });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const completed = !!task.completed;
  const isRepeating = !!task.repeat_freq;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={[
        "group rounded-2xl border bg-white p-3 shadow-sm",
        "hover:shadow-md transition",
        isDragging ? "opacity-60 ring-2 ring-zinc-400" : "",
        completed ? "bg-zinc-50" : "",
        isRepeating ? "border-dashed" : "",
      ].join(" ")}
      {...attributes}
      {...listeners}
    >
      <div className="flex items-start gap-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggle?.(task);
          }}
          className="mt-0.5 text-zinc-500 hover:text-zinc-800"
          title={completed ? "Mark incomplete" : "Mark complete"}
        >
          {completed ? (
            <CheckCircle2 className="w-5 h-5 text-green-600" />
          ) : (
            <Circle className="w-5 h-5" />
          )}
        </button>

        <div className="flex-1 min-w-0">
          <div
            className={[
              "text-sm font-medium leading-snug",
              completed ? "line-through text-zinc-400" : "text-zinc-900",
            ].join(" ")}
          >
            {task.title}
          </div>

          {task.notes && (
            <div className="text-xs text-zinc-500 mt-1 line-clamp-2">
              {task.notes}
            </div>
          )}

          <div className="flex items-center gap-2 mt-2">
            {isRepeating && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-700">
                Repeats
              </span>
            )}
            {task.priority && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-zinc-900 text-white">
                {task.priority}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit?.(task);
            }}
            className="p-1 text-zinc-500 hover:text-zinc-900"
            title="Edit"
          >
            <Pencil className="w-4 h-4" />
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete?.(task);
            }}
            className="p-1 text-zinc-500 hover:text-red-600"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
