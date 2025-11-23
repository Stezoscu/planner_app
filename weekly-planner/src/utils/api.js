// src/utils/api.js
import { getAuth } from "firebase/auth";

export async function authFetch(path, options = {}) {
  const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
  const url = path.startsWith("http") ? path : `${base}${path}`;

  const auth = getAuth();
  const currentUser = auth.currentUser;
  let token = null;

  // --- Retrieve ID token if user is logged in ---
  if (currentUser) {
    try {
      token = await currentUser.getIdToken();
    } catch (err) {
      console.warn("⚠️ Could not get Firebase token:", err);
    }
  }

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  // --- Handle expired/unauthorised sessions ---
  if (res.status === 401) {
    console.warn("🔒 Unauthorized — possible expired token. Signing out.");
    await auth.signOut();
    window.location.reload();
    return;
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error (${res.status}): ${text}`);
  }

  const type = res.headers.get("content-type") || "";
  return type.includes("application/json") ? res.json() : res.text();
}
