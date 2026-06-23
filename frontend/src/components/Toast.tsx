"use client";

import React, { useEffect, useState } from "react";

export interface ToastMessage {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

export function showToast(message: string, type: "success" | "error" | "info" = "success") {
  if (typeof window !== "undefined") {
    const event = new CustomEvent("show-toast", { detail: { message, type } });
    window.dispatchEvent(event);
  }
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const handleToast = (e: Event) => {
      const customEvent = e as CustomEvent<{ message: string; type: "success" | "error" | "info" }>;
      const newToast: ToastMessage = {
        id: Math.random().toString(36).substr(2, 9),
        ...customEvent.detail,
      };
      setToasts((prev) => [...prev, newToast]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== newToast.id));
      }, 3000);
    };

    window.addEventListener("show-toast", handleToast);
    return () => window.removeEventListener("show-toast", handleToast);
  }, []);

  return (
    <div className="fixed bottom-6 right-6 z-[200] flex flex-col gap-3 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`px-4 py-3 rounded-xl shadow-2xl border text-sm font-semibold flex items-center gap-2 animate-in slide-in-from-bottom-5 fade-in duration-300 ${
            toast.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 backdrop-blur-md"
              : toast.type === "error"
              ? "bg-rose-500/10 border-rose-500/30 text-rose-400 backdrop-blur-md"
              : "bg-indigo-500/10 border-indigo-500/30 text-indigo-400 backdrop-blur-md"
          }`}
        >
          {toast.type === "success" && (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )}
          {toast.message}
        </div>
      ))}
    </div>
  );
}
