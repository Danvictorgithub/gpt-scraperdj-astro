import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import auth from "auth-astro";

import node from "@astrojs/node";

// https://astro.build/config
export default defineConfig({
  security: {
    checkOrigin: true
  },
  integrations: [tailwind(), auth()],
  output: "hybrid",
  adapter: node({
    mode: "standalone"
  })
});