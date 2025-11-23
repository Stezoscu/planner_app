// src/views/WeekView.jsx
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { format, isSameDay } from "date-fns";
import { Plus } from "lucide-react";
import { Card, Button } from "../components/UI";
import TaskEditor from "../components/TaskEditor";
import TaskCard from "../components/TaskCard";
import { authFetch } from "../utils/api";
import { toISODate, getWeekRange } from "../utils/dates";

import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";

// Small helper component so each day column is a droppable zone
function DayColumn({ id, children, isToday }) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={[
        "rounded-3xl p-3 bg-zinc-50 border border-zinc-200",
        "min-h-[140px] flex flex-col gap-2 transition",
        isOver ? "border-zinc-400 bg-zinc-100/70" : "hover:border-zinc-300",
        isToday ? "ring-1 ring-zinc-300" : "",
      ].join(" ")}
    >
      {children}
    </div>
  );
}

export default function WeekView({ selectedDate, onSelectDate }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openEditor, setOpenEditor] = useState(false);
  const [editing, setEditing] = useState(null);

  const { start, end, days } = useMemo(
    () => getWeekRange(selectedDate),
    [selectedDate]
  );

  // --- Fetch tasks for the week ---
  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      const data = await authFetch(`/api/tasks?from=${start}&to=${end}`);
      setTasks(Array.isArray(data) ? data : data.tasks || []);
      setError("");
    } catch (e) {
      console.error("Error fetching tasks:", e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [start, end]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // --- Group tasks by day ---
  const tasksByDate = useMemo(() => {
    const map = {};
    for (const d of days) map[toISODate(d)] = [];

    for (const t of tasks) {
      const key = (t.due_date || "").slice(0, 10);
      if (!key) continue;
      if (!map[key]) map[key] = [];
      map[key].push(t);
    }

    // keep stable sort order if backend doesn't guarantee one
    for (const k of Object.keys(map)) {
      map[k].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));
    }

    return map;
  }, [tasks, days]);

  // --- Handlers ---
  const onCreate = () => {
    setEditing(null);
    setOpenEditor(true);
  };

  const onEdit = (task) => {
    setEditing(task);
    setOpenEditor(true);
  };

  const onDelete = async (task) => {
    if (!confirm("Delete this task?")) return;
    await authFetch(`/api/tasks/${task.id}`, { method: "DELETE" });
    await fetchTasks();
  };

  // ✅ Toggle completion for one specific occurrence
  const onToggleComplete = async (task) => {
    try {
      await authFetch(`/api/tasks/${task.id}/toggle`, {
        method: "PATCH",
        body: JSON.stringify({ date: task.due_date }),
      });
      await fetchTasks();
    } catch (err) {
      alert(`Failed to toggle completion: ${err.message}`);
    }
  };

  // --- dnd-kit setup ---
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  // Reorder within same column (optimistic UI) + update due date on cross-column drop
  const handleDragEnd = async (event) => {
    const { active, over } = event;
    if (!over) return;

    const activeTask = active.data?.current?.task;
    const overTask = over.data?.current?.task;

    if (!activeTask) return;

    // block dragging repeating tasks for now
    if (activeTask.repeat_freq) {
      alert("Repeating tasks can’t be dragged yet — edit the series instead.");
      return;
    }

    const fromDate = (activeTask.due_date || "").slice(0, 10);

    // If hovering over another task, infer that task’s column date.
    // If hovering over empty column, over.id is the column date.
    const toDate = overTask
      ? (overTask.due_date || "").slice(0, 10)
      : over.id;

    if (!toDate) return;
    if (fromDate === toDate && active.id === over.id) return;

    // Same-column reorder (pure UI ordering)
    if (fromDate === toDate && overTask) {
      const list = tasksByDate[fromDate] || [];
      const oldIndex = list.findIndex(
        (t) =>
          `${t.id}-${(t.due_date || "").slice(0, 10)}` === active.id
      );
      const newIndex = list.findIndex(
        (t) =>
          `${t.id}-${(t.due_date || "").slice(0, 10)}` === over.id
      );

      if (oldIndex !== -1 && newIndex !== -1 && oldIndex !== newIndex) {
        const reordered = arrayMove(list, oldIndex, newIndex);

        // optimistic update
        const flattened = [];
        for (const dayKey of Object.keys(tasksByDate)) {
          if (dayKey === fromDate) flattened.push(...reordered);
          else flattened.push(...tasksByDate[dayKey]);
        }
        setTasks(flattened);

        // optional: if you later add sort_order persistence, PATCH here.
      }
      return;
    }

    // Cross-column move → update due_date in backend
    try {
      await authFetch(`/api/tasks/${activeTask.id}`, {
        method: "PATCH",
        body: JSON.stringify({ due_date: toDate }),
      });
      await fetchTasks();
    } catch (err) {
      alert(`Failed to move task: ${err.message}`);
      await fetchTasks();
    }
  };

  // --- Render ---
  return (
    <Card className="bg-white/80 backdrop-blur">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold">
            Week of {format(days[0], "EEE d MMM")}
          </h2>
          <p className="text-zinc-600 text-sm">
            {format(days[0], "d MMM")} – {format(days[6], "d MMM yyyy")}{" "}
            (Europe/London)
          </p>
        </div>
        <Button
          onClick={onCreate}
          className="inline-flex items-center gap-2 bg-zinc-900 text-white border-zinc-900 hover:bg-zinc-800"
        >
          <Plus className="w-4 h-4" /> New Task
        </Button>
      </div>

      {loading && <div className="text-zinc-600">Loading week…</div>}
      {error && <div className="text-red-600">{error}</div>}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
          {days.map((d) => {
            const key = toISODate(d);
            const list = tasksByDate[key] || [];
            const occIds = list.map(
              (t) => `${t.id}-${(t.due_date || "").slice(0, 10)}`
            );

            return (
              <DayColumn key={key} id={key} isToday={isSameDay(d, new Date())}>
                <div className="flex items-center justify-between mb-2">
                  <button
                    onClick={() => onSelectDate(d)}
                    className="text-sm font-semibold hover:underline"
                  >
                    {format(d, "EEE")}
                    <span className="ml-2 text-zinc-500 font-normal">
                      {format(d, "d")}
                    </span>
                  </button>
                  {isSameDay(d, new Date()) && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-900 text-white">
                      Today
                    </span>
                  )}
                </div>

                <SortableContext
                  items={occIds}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="flex-1 flex flex-col gap-2">
                    {list.length === 0 && (
                      <div className="text-sm text-zinc-500 italic">
                        No tasks
                      </div>
                    )}

                    {list.map((t) => (
                      <TaskCard
                        key={`${t.id}-${(t.due_date || "").slice(0, 10)}`}
                        task={t}
                        onEdit={onEdit}
                        onDelete={onDelete}
                        onToggle={onToggleComplete}
                      />
                    ))}
                  </div>
                </SortableContext>
              </DayColumn>
            );
          })}
        </div>
      </DndContext>

      <TaskEditor
        open={openEditor}
        initialDate={toISODate(selectedDate)}
        task={editing}
        onClose={() => setOpenEditor(false)}
        onSaved={async () => {
          setOpenEditor(false);
          await fetchTasks();
        }}
      />
    </Card>
  );
}
