import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { getInitialTheme } from "./contexts/ThemeContext";
import "./styles/global.css";

document.documentElement.setAttribute("data-theme", getInitialTheme());

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
