import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development, /api calls are forwarded to the FastAPI server on port 8000,
// so the browser sees one origin and we avoid CORS headaches.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
  test: { environment: "node" },
});
