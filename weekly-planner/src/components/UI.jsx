// src/components/UI.jsx
import React from "react";

export function Button({ className = "", children, ...rest }) {
  return (
    <button
      className={`px-3 py-2 rounded-2xl border border-zinc-200 bg-white shadow-sm hover:shadow transition ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

export function Card({ className = "", children }) {
  return (
    <div
      className={`rounded-2xl border border-zinc-200 bg-white shadow-sm p-4 ${className}`}
    >
      {children}
    </div>
  );
}

export function Input({ className = "", ...rest }) {
  return (
    <input
      className={`border border-zinc-300 rounded-xl px-3 py-2 w-full text-sm focus:outline-none focus:ring-2 focus:ring-zinc-300 transition ${className}`}
      {...rest}
    />
  );
}

export function Textarea({ className = "", ...rest }) {
  return (
    <textarea
      className={`border border-zinc-300 rounded-xl px-3 py-2 w-full text-sm focus:outline-none focus:ring-2 focus:ring-zinc-300 transition ${className}`}
      {...rest}
    />
  );
}

export function Modal({ open, onClose, title, children, footer }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white w-full max-w-xl rounded-3xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-zinc-800 transition"
          >
            ✕
          </button>
        </div>
        <div>{children}</div>
        {footer && <div className="mt-6 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}
