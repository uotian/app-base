import type { NextConfig } from "next";

const config: NextConfig = {
  output: "export",
  agentRules: false,
  trailingSlash: true,
  images: { unoptimized: true },
};

export default config;
