import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import LogoutButton from "./LogoutButton";
import "./Sidebar.css";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [avatarFailed, setAvatarFailed] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const avatarUrl = user?.user_metadata?.avatar_url as string | undefined;
  const name =
    (user?.user_metadata?.full_name as string | undefined) ??
    (user?.user_metadata?.name as string | undefined) ??
    user?.email ??
    "Usuário";

  function handleSwitchSheet() {
    onClose();
    navigate("/connect-sheet?trocar=1");
  }

  return (
    <>
      <div
        className={`sidebar-overlay ${isOpen ? "sidebar-overlay--visible" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside className={`sidebar ${isOpen ? "sidebar--open" : ""}`} aria-hidden={!isOpen}>
        <div className="sidebar-profile">
          {avatarUrl && !avatarFailed ? (
            <img
              className="sidebar-avatar"
              src={avatarUrl}
              alt=""
              referrerPolicy="no-referrer"
              onError={() => setAvatarFailed(true)}
            />
          ) : (
            <div className="sidebar-avatar sidebar-avatar--fallback" aria-hidden="true">
              {name.charAt(0).toUpperCase()}
            </div>
          )}
          <span className="sidebar-name">{name}</span>
        </div>

        <nav className="sidebar-actions">
          <button type="button" onClick={toggleTheme}>
            {theme === "light" ? "Tema escuro" : "Tema claro"}
          </button>
          <button type="button" onClick={handleSwitchSheet}>
            Trocar planilha
          </button>
          <LogoutButton />
        </nav>
      </aside>
    </>
  );
}
