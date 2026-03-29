import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for the multi-stage Docker build: copies only the minimum files
  // needed to run the server into .next/standalone, keeping the image small.
  output: 'standalone',
};

export default nextConfig;
