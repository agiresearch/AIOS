/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: false,
    async rewrites() {
        return [
          {
            source: '/agents',
            destination: '/agents?p=0',
          },
          {
            source: '/',
            destination: '/chat',
          },
          
        ]
      },
};

export default nextConfig;
