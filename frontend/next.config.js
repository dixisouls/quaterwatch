/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ["lh3.googleusercontent.com"],
  },
  async rewrites() {
    return [
      {
        source: "/api/jobs/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/jobs/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
