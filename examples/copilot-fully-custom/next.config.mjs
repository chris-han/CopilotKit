import path from "node:path";

const nextConfig = {
  env: {
    COPILOTKIT_TELEMETRY_DISABLED: "true",
  },
  webpack: (config) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = config.resolve.alias || {};
    config.resolve.alias["@segment/analytics-node"] = path.resolve(
      process.cwd(),
      "stubs/segment-analytics-node.ts",
    );
    return config;
  },
};

export default nextConfig;
