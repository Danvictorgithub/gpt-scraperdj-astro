import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import auth from "auth-astro";
import node from "@astrojs/node";
import react from "@astrojs/react";
import icon from "astro-icon";

import vercel from "@astrojs/vercel/serverless";

// https://astro.build/config
export default defineConfig({
  security: {
    checkOrigin: true
  },
  integrations: [icon(), tailwind(), react(), auth()],
  output: "server",
  adapter: vercel()
});