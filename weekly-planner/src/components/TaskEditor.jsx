// src/components/TaskEditor.jsx
import React, { useEffect, useState } from "react";
import { Card, Button, Input, Textarea } from "./UI";
import { authFetch } from "../utils/api";

export default function TaskEditor({ open, initialDate, task, onClose, onSaved }) {
  const isEditing = !!task;

  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [selectedDate, setSelectedDate] = useState(initialDate || "");
  const [repeatFreq, setRepeatFreq] = useState("");
  const [repeatInterval, setRepeatInterval] = useState(1);
  const [repeatUntil, setRepeatUntil] = useState("");
  const [repeatCount, setRepeatCount] = useState("");
  const [saving, setSaving] = useState(false);

  // --- Pre-fill when editing ---
  useEffect(() => {
    if (task) {
      setTitle(task.title || "");
      setNotes(task.notes || "");
      setSelectedDate(task.due_date ? task.due_date.slice(0, 10) : initialDate || "");

      // 🔧 Handle both nested repeat object and flat DB fields
      const r = task.repeat ?? {
        freq: task.repeat_freq,
        interval: task.repeat_interval,
        until: task.repeat_until,
        count: task.repeat_count,
      };

      setRepeatFreq(r?.freq || "");
      setRepeatInterval(r?.interval || 1);

      // Ensure date-only format for <input type="date">
      if (r?.until) {
        try {
          const d = new Date(r.until);
          setRepeatUntil(!isNaN(d) ? d.toISOString().slice(0, 10) : "");
        } catch {
          setRepeatUntil("");
        }
      } else {
        setRepeatUntil("");
      }

      setRepeatCount(r?.count || "");
    } else {
      // Reset to defaults when adding new
      setTitle("");
      setNotes("");
      setSelectedDate(initialDate || "");
      setRepeatFreq("");
      setRepeatInterval(1);
      setRepeatUntil("");
      setRepeatCount("");
    }
  }, [task, initialDate]);

  if (!open) return null;

  async function handleSave() {
    try {
      setSaving(true);

      const body = {
        title,
        notes,
        completed: task?.completed ?? false,
        due_date: isEditing && task?.due_date ? task.due_date : selectedDate,
        repeat: repeatFreq
          ? {
              freq: repeatFreq,
              interval: Number(repeatInterval) || 1,
              until: repeatUntil || null,
              count: repeatCount ? Number(repeatCount) : null,
            }
          : null,
      };

      const endpoint = isEditing ? `/api/tasks/${task.id}` : "/api/tasks";
      const method = isEditing ? "PUT" : "POST";

      const res = await authFetch(endpoint, {
        method,
        body: JSON.stringify(body),
      });

      if (!res || res.error) throw new Error(res?.error || "Failed to save task");

      // ✅ Reset fields after save (for add mode)
      if (!isEditing) {
        setTitle("");
        setNotes("");
        setRepeatFreq("");
        setRepeatInterval(1);
        setRepeatUntil("");
        setRepeatCount("");
        setSelectedDate(initialDate || "");
      }

      onSaved?.();
      onClose?.();
    } catch (err) {
      alert(`Error saving task: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <Card className="w-full max-w-md bg-white p-6">
        <h2 className="text-lg font-semibold mb-3">
          {isEditing ? "Edit Task" : "New Task"}
        </h2>

        {/* --- Task Fields --- */}
        <Input
          placeholder="Task title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="mb-3"
        />
        <Textarea
          rows={3}
          placeholder="Notes (optional)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="mb-3"
        />

        {/* --- Date selector (only when creating new task) --- */}
        {!isEditing && (
          <label className="block mb-3 text-sm text-zinc-700">
            Date
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full border border-zinc-300 rounded-xl px-3 py-2 mt-1"
            />
          </label>
        )}

        {/* --- Repeat Options --- */}
        <div className="mb-3 border-t pt-3">
          <h3 className="text-sm font-semibold mb-2">Repeat Options</h3>

          <label className="block mb-2 text-sm text-zinc-700">
            Frequency
            <select
              value={repeatFreq}
              onChange={(e) => setRepeatFreq(e.target.value)}
              className="w-full border border-zinc-300 rounded-xl px-3 py-2 mt-1"
            >
              <option value="">Does not repeat</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          </label>

          {repeatFreq && (
            <>
              <label className="block mb-2 text-sm text-zinc-700">
                Every
                <input
                  type="number"
                  min="1"
                  value={repeatInterval}
                  onChange={(e) => setRepeatInterval(e.target.value)}
                  className="w-20 border border-zinc-300 rounded-xl px-2 py-1 ml-2"
                />
                {repeatFreq === "daily" && " days"}
                {repeatFreq === "weekly" && " weeks"}
                {repeatFreq === "monthly" && " months"}
                {repeatFreq === "yearly" && " years"}
              </label>

              <label className="block mb-2 text-sm text-zinc-700">
                Until (optional)
                <input
                  type="date"
                  value={repeatUntil}
                  onChange={(e) => setRepeatUntil(e.target.value)}
                  className="w-full border border-zinc-300 rounded-xl px-3 py-2 mt-1"
                />
              </label>

              <label className="block mb-2 text-sm text-zinc-700">
                Or stop after (optional)
                <input
                  type="number"
                  min="1"
                  value={repeatCount}
                  onChange={(e) => setRepeatCount(e.target.value)}
                  className="w-24 border border-zinc-300 rounded-xl px-2 py-1 ml-2"
                />
                {" occurrences"}
              </label>
            </>
          )}
        </div>

        {/* --- Buttons --- */}
        <div className="flex justify-end gap-2 mt-4">
          <Button onClick={onClose} className="bg-zinc-100">
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || !title.trim()}
            className="bg-zinc-900 text-white"
          >
            {saving ? "Saving…" : isEditing ? "Update Task" : "Save Task"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
