/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
 resolve: {
 extensions: [".ts", ".tsx", ".mjs", ".js", ".mts", ".jsx", ".json"],
 },
 plugins: [react()],
 server: {
  host: "127.0.0.1",
  port: 5173,
  proxy: {
   "/api": {
    target: "http://127.0.0.1:8000",
    changeOrigin: true,
   },
  },
 },
 test: {
 globals: true,
 environment: "jsdom",
 setupFiles: ["./vitest.setup.ts"],
 coverage: {
 provider: "v8",
 reporter: ["text", "html"],
 include: ["src/App.tsx", "src/api.ts", "src/lib/**/*.ts", "src/state/**/*.ts"],
 thresholds: {
 lines:90,
 statements:90,
 functions:80,
 branches:80,
 },
 },
 },
});
