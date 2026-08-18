import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { Session, User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabaseClient";
import { api } from "../services/api";

interface AuthContextValue {
  session: Session | null;
  user: User | null;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, newSession) => {
      setSession(newSession);
      setLoading(false);

      const isMicrosoftLogin =
        event === "SIGNED_IN" && newSession?.user.app_metadata.provider === "azure";

      if (isMicrosoftLogin) {
        if (!newSession.provider_token || !newSession.provider_refresh_token) {
          console.error(
            "Login com Microsoft não retornou os tokens de acesso esperados — a conexão com o Excel Online não vai funcionar até logar novamente.",
          );
        } else {
          api
            .post("/config/microsoft-token", {
              access_token: newSession.provider_token,
              refresh_token: newSession.provider_refresh_token,
              expires_in: newSession.expires_in ?? 3600,
            })
            .catch((err) => {
              console.error("Não foi possível salvar o acesso à conta Microsoft:", err);
            });
        }
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <AuthContext.Provider value={{ session, user: session?.user ?? null, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
}
