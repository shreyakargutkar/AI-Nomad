/** @type {import('next').NextConfig} */
const nextConfig = {
  async redirects() {
    return [
      { source: '/search', destination: '/features/cultural-intelligence', permanent: true },
      { source: '/chatbot', destination: '/', permanent: false },
    ];
  },
};

export default nextConfig;
