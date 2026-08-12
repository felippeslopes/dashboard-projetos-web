import { useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabaseClient";

export default function LogoutButton() {
  const navigate = useNavigate();

  async function handleLogout() {
    await supabase.auth.signOut();
    navigate("/login", { replace: true });
  }

  return (
    <button type="button" onClick={handleLogout}>
      Sair
    </button>
  );
}
