// src/App.jsx
import React from "react";
import { Calendar as CalendarIcon, LogIn } from "lucide-react";
import { AuthProvider, useAuth } from "./context/AuthContext"; // ✅ moved from utils → context
import { Card, Button } from "./components/UI";
import Shell from "./Shell";

function SignInScreen() {
  const { signIn } = useAuth();

  return (
    <div className="min-h-screen grid place-items-center p-6 bg-zinc-50">
      <Card className="max-w-md text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <CalendarIcon className="w-6 h-6" />
          <h1 className="text-2xl font-semibold">Weekly Planner</h1>
        </div>
        <p className="text-zinc-600 mb-4">Sign in with Google to get started.</p>
        <Button onClick={signIn} className="inline-flex items-center gap-2">
          <LogIn className="w-4 h-4" /> Continue with Google
        </Button>
      </Card>
    </div>
  );
}

function MainApp() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center">
        <div className="text-zinc-600">Loading…</div>
      </div>
    );
  }

  if (!user) return <SignInScreen />;
  return <Shell />;
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
