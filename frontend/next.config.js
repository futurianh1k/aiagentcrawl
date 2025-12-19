/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone 모드 활성화 (Docker 최적화)
  output: 'standalone',
  
  // 환경 변수 설정
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  },

  // 이미지 최적화 설정
  images: {
    domains: [],
    unoptimized: false,
  },

  // 리다이렉트 설정
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
