import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { supabase } from "../lib/supabaseClient";

export default function Login() {
  const { session, loading } = useAuth();

  if (loading) {
    return <div>Carregando...</div>;
  }

  if (session) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleLogin() {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin },
    });
    if (error) {
      console.error("Erro ao iniciar login com Google:", error.message);
    }
  }

  return (
    <div>
      <h1>Dashboard de Projetos Web</h1>
      <button onClick={handleLogin}>Entrar com Google</button>
    </div>
  );
}
