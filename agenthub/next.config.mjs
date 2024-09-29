/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: false,

    images: {
        remotePatterns: [
          {
            protocol: 'https',
            hostname: 'supabase.com',
            port: '',
            pathname: '**',
          },
        ],
      },
};

export default nextConfig;
