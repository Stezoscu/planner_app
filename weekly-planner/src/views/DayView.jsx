// src/views/DayView.jsx
import React, { useCallback, useEffect, useState } from "react";
import { addDays, format } from "date-fns";
import { Plus, Sun } from "lucide-react";
import { Card, Button } from "../components/UI";
import TaskList from "../components/TaskList";
import AgendaView from "./AgendaView";
import TaskEditor from "../components/TaskEditor";
import { authFetch } from "../utils/api";
import { toISODate } from "../utils/dates";

export default function DayView({ date }) {
  const iso = toISODate(date);
  const [tasks, setTasks] = useState([]);
  const [agenda, setAgenda] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openEditor, setOpenEditor] = useState(false);
  const [editing, setEditing] = useState(null);

  // --- Fetch all tasks + agenda ---
  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      const [taskRes, agendaRes] = await Promise.all([
        authFetch(`/api/tasks?from=${iso}&to=${toISODate(addDays(date, 1))}`),
        authFetch(`/api/agenda?date=${iso}`),
      ]);
      setTasks(taskRes || []);
      setAgenda(agendaRes.items || []);
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [date, iso]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

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
    await fetchAll();
  };

  // ✅ NEW — per-day toggle using /toggle endpoint
  const onToggleComplete = async (task) => {
    try {
      await authFetch(`/api/tasks/${task.id}/toggle`, {
        method: "PATCH",
        body: JSON.stringify({ date: task.due_date }),
      });
      await fetchAll();
    } catch (err) {
      alert(`Failed to toggle completion: ${err.message}`);
    }
  };

  // --- UI ---
  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold">{format(date, "EEEE d MMMM")}</h2>
          <p className="text-zinc-600 text-sm">Your day and tasks</p>
        </div>
        <Button onClick={onCreate} className="inline-flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Task
        </Button>
      </div>

      {loading && <div className="text-zinc-600">Loading day…</div>}
      {error && <div className="text-red-600">{error}</div>}

      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <h3 className="font-medium mb-2">Tasks</h3>
          <TaskList
            tasks={tasks}
            onEdit={onEdit}
            onDelete={onDelete}
            onToggle={onToggleComplete}
          />
        </div>
        <div>
          <h3 className="font-medium mb-2 inline-flex items-center gap-2">
            <Sun className="w-4 h-4" /> Agenda
          </h3>
          <AgendaView agenda={agenda} />
        </div>
      </div>

      <TaskEditor
        open={openEditor}
        initialDate={iso}
        task={editing}
        onClose={() => setOpenEditor(false)}
        onSaved={async () => {
          setOpenEditor(false);
          await fetchAll();
        }}
      />
    </Card>
  );
}
