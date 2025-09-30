import { existsSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const configPath = join(process.cwd(), "tailwind.config.ts");

if (existsSync(configPath)) {
  process.exit(0);
}

const configContent = `import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./hooks/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
`;

writeFileSync(configPath, configContent);
console.log("Created tailwind.config.ts");
