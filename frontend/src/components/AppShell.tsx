import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import "./AppShell.css";

export default function AppShell() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  return (
    <div className="app-shell">
      <button
        type="button"
        className="menu-trigger"
        aria-label="Abrir menu"
        onClick={() => setIsOpen(true)}
      >
        ☰
      </button>
      <Sidebar isOpen={isOpen} onClose={() => setIsOpen(false)} />
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
