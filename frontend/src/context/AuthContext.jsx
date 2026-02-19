// context/AuthContext.jsx
// Fix: loading starts true so Navbar shows skeleton immediately,
// preventing the flash of "Get Started" before auth resolves.

import { createContext, useContext, useEffect, useState } from "react";
import { getMe, logout } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // Start as true — we're always loading until getMe resolves
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const signOut = async () => {
    await logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);