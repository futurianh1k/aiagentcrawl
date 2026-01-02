'use client';

import Link from 'next/link';
import { useState } from 'react';

export default function LandingGradient() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      {/* Navigation */}
      <nav className="fixed w-full bg-gray-950/80 backdrop-blur-md z-50 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                NewsAI
              </Link>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <Link href="#features" className="text-gray-300 hover:text-white transition-colors">
                Features
              </Link>
              <Link href="#pricing" className="text-gray-300 hover:text-white transition-colors">
                Pricing
              </Link>
              <Link href="/auth/login" className="text-gray-300 hover:text-white transition-colors">
                Login
              </Link>
              <Link
                href="/auth/register"
                className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-2 rounded-full hover:shadow-lg hover:shadow-purple-500/50 transition-all hover:scale-105"
              >
                Get Started
              </Link>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden p-2 rounded-md text-gray-300 hover:text-white"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-gray-800 bg-gray-950">
            <div className="px-2 pt-2 pb-3 space-y-1">
              <Link href="#features" className="block px-3 py-2 text-gray-300 hover:text-white">
                Features
              </Link>
              <Link href="#pricing" className="block px-3 py-2 text-gray-300 hover:text-white">
                Pricing
              </Link>
              <Link href="/auth/login" className="block px-3 py-2 text-gray-300 hover:text-white">
                Login
              </Link>
              <Link
                href="/auth/register"
                className="block px-3 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg text-center"
              >
                Get Started
              </Link>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Gradient Orbs */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full filter blur-3xl opacity-20"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full filter blur-3xl opacity-20"></div>

        <div className="max-w-7xl mx-auto text-center relative z-10">
          <div className="inline-block mb-4">
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-full text-sm font-medium">
              ✨ Powered by Advanced AI
            </span>
          </div>

          <h1 className="text-5xl md:text-8xl font-bold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Transform News
            </span>
            <br />
            <span className="text-white">Into Insights</span>
          </h1>

          <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
            Harness the power of AI to understand public sentiment.
            <br />
            <span className="text-gray-500">Analyze thousands of articles in seconds.</span>
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
            <Link
              href="/auth/register"
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-10 py-5 rounded-full text-lg font-semibold hover:shadow-2xl hover:shadow-purple-500/50 transition-all hover:scale-105"
            >
              Start Analyzing Free
            </Link>
            <Link
              href="/dashboard"
              className="border-2 border-gray-700 text-white px-10 py-5 rounded-full text-lg font-semibold hover:bg-gray-800 transition-all group"
            >
              See Demo
              <span className="inline-block ml-2 group-hover:translate-x-1 transition-transform">→</span>
            </Link>
          </div>

          {/* Animated Stats */}
          <div className="grid grid-cols-3 gap-8 max-w-3xl mx-auto">
            {[
              { value: '10K+', label: 'Articles Analyzed', gradient: 'from-blue-400 to-cyan-400' },
              { value: '95%', label: 'Accuracy Rate', gradient: 'from-purple-400 to-pink-400' },
              { value: '<2s', label: 'Processing Time', gradient: 'from-pink-400 to-red-400' },
            ].map((stat, i) => (
              <div key={i} className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-100 blur-xl transition-opacity from-blue-500 to-purple-500"></div>
                <div className="relative bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6 hover:border-gray-700 transition-colors">
                  <div className={`text-4xl font-bold bg-gradient-to-r ${stat.gradient} bg-clip-text text-transparent mb-2`}>
                    {stat.value}
                  </div>
                  <div className="text-gray-400 text-sm">{stat.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-6xl font-bold mb-4">
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Powerful Features
              </span>
            </h2>
            <p className="text-xl text-gray-400">
              Everything you need to master news sentiment analysis
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: '⚡',
                title: 'Lightning Fast',
                desc: 'Process thousands of articles in under 2 seconds with our optimized AI engine.',
                gradient: 'from-yellow-400 to-orange-500'
              },
              {
                icon: '📊',
                title: 'Beautiful Visuals',
                desc: 'Interactive charts and graphs that make complex data easy to understand.',
                gradient: 'from-blue-400 to-cyan-500'
              },
              {
                icon: '🤖',
                title: 'AI-Powered',
                desc: 'Advanced machine learning models trained on millions of articles.',
                gradient: 'from-purple-400 to-pink-500'
              },
              {
                icon: '🌐',
                title: 'Multi-Source',
                desc: 'Aggregate news from Naver, Google, and dozens of other platforms.',
                gradient: 'from-green-400 to-emerald-500'
              },
              {
                icon: '💾',
                title: 'Export Anywhere',
                desc: 'Download your analysis in CSV, JSON, or integrate via our API.',
                gradient: 'from-red-400 to-pink-500'
              },
              {
                icon: '🔒',
                title: 'Secure & Private',
                desc: 'Enterprise-grade security with end-to-end encryption.',
                gradient: 'from-indigo-400 to-purple-500'
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="relative group"
              >
                <div className={`absolute inset-0 bg-gradient-to-r ${feature.gradient} rounded-2xl opacity-0 group-hover:opacity-10 blur-xl transition-opacity`}></div>
                <div className="relative bg-gray-900/50 backdrop-blur-sm border border-gray-800 p-8 rounded-2xl hover:border-gray-700 transition-all">
                  <div className="text-5xl mb-4">{feature.icon}</div>
                  <h3 className={`text-2xl font-bold mb-3 bg-gradient-to-r ${feature.gradient} bg-clip-text text-transparent`}>
                    {feature.title}
                  </h3>
                  <p className="text-gray-400 leading-relaxed">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8 relative">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-6xl font-bold mb-4">
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Choose Your Plan
              </span>
            </h2>
            <p className="text-xl text-gray-400">
              Start free. Scale as you grow.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Free Plan */}
            <div className="bg-gray-900/50 backdrop-blur-sm border-2 border-gray-800 rounded-3xl p-8 hover:border-gray-700 transition-colors">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-white mb-2">Free</h3>
                <div className="text-6xl font-bold text-white mb-2">$0</div>
                <p className="text-gray-400">Perfect to get started</p>
              </div>

              <ul className="space-y-4 mb-8">
                {[
                  { text: 'Up to 3 articles per search', included: true },
                  { text: 'Basic sentiment analysis', included: true },
                  { text: 'Search history', included: false },
                  { text: 'Data export', included: false },
                ].map((item, i) => (
                  <li key={i} className="flex items-start">
                    {item.included ? (
                      <svg className="w-6 h-6 text-green-400 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="w-6 h-6 text-gray-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    )}
                    <span className={item.included ? 'text-gray-300' : 'text-gray-600'} dangerouslySetInnerHTML={{ __html: item.text.includes('3') ? item.text.replace('3', '<strong class="text-white">3</strong>') : item.text }} />
                  </li>
                ))}
              </ul>

              <Link
                href="/dashboard"
                className="block w-full text-center bg-gray-800 text-white px-6 py-4 rounded-full font-semibold hover:bg-gray-700 transition-colors"
              >
                Try Free Now
              </Link>
            </div>

            {/* Premium Plan */}
            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-3xl blur opacity-75 group-hover:opacity-100 transition duration-1000"></div>
              <div className="relative bg-gray-900 rounded-3xl p-8">
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-2 rounded-full text-sm font-bold shadow-lg">
                    ⭐ MOST POPULAR
                  </span>
                </div>

                <div className="text-center mb-8 mt-4">
                  <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
                    Premium
                  </h3>
                  <div className="text-6xl font-bold text-white mb-2">Free</div>
                  <p className="text-gray-400">Unlimited power users</p>
                </div>

                <ul className="space-y-4 mb-8">
                  {[
                    'Up to <strong class="text-white">50 articles</strong> per search',
                    'Advanced AI analysis & summaries',
                    'Full search history & saved results',
                    'Export to CSV/JSON',
                    'Priority support',
                    'Early access to new features'
                  ].map((item, i) => (
                    <li key={i} className="flex items-start">
                      <svg className="w-6 h-6 text-green-400 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300" dangerouslySetInnerHTML={{ __html: item }} />
                    </li>
                  ))}
                </ul>

                <Link
                  href="/auth/register"
                  className="block w-full text-center bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-4 rounded-full font-semibold hover:shadow-2xl hover:shadow-purple-500/50 transition-all hover:scale-105"
                >
                  Get Started Free
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 opacity-10"></div>
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8 relative z-10">
          <h2 className="text-5xl md:text-7xl font-bold mb-8">
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Ready to dive in?
            </span>
          </h2>
          <p className="text-2xl text-gray-400 mb-12">
            Join thousands analyzing news with AI
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link
              href="/auth/register"
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-12 py-5 rounded-full text-xl font-bold hover:shadow-2xl hover:shadow-purple-500/50 transition-all hover:scale-105"
            >
              Start Free Trial
            </Link>
            <Link
              href="/dashboard"
              className="border-2 border-gray-700 text-white px-12 py-5 rounded-full text-xl font-bold hover:bg-gray-800 transition-all"
            >
              Try Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-950 border-t border-gray-900 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div>
              <div className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-4">
                NewsAI
              </div>
              <p className="text-gray-500 text-sm">
                AI-powered news sentiment analysis platform.
              </p>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><Link href="#features" className="hover:text-white transition-colors">Features</Link></li>
                <li><Link href="#pricing" className="hover:text-white transition-colors">Pricing</Link></li>
                <li><Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-gray-900 text-center text-gray-500 text-sm">
            © 2024 NewsAI. All rights reserved.
          </div>
        </div>
      </footer>

      <style jsx>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}
