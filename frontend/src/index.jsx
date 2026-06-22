import React from "react";
import { createRoot } from "react-dom/client";
import RouterApp from "./App.jsx"; // imports the existing App.js in project root

const container = document.getElementById("root");
const root = createRoot(container);
root.render(
  <React.StrictMode>
    <RouterApp />
  </React.StrictMode>
);
