'use client';

import Link from 'next/link';
import { useState } from 'react';

export default function LandingSimple() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="pt-24 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6 leading-tight">
            AI-Powered News
            <br />
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Sentiment Analysis
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-12 max-w-3xl mx-auto leading-relaxed">
            Understand public opinion in seconds. Analyze news sentiment with advanced AI technology.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/auth/register"
              className="bg-gray-900 text-white px-8 py-4 rounded-full text-lg font-medium hover:bg-gray-800 transition-all hover:scale-105"
            >
              Start Free Trial
            </Link>
            <Link
              href="/dashboard"
              className="border-2 border-gray-900 text-gray-900 px-8 py-4 rounded-full text-lg font-medium hover:bg-gray-50 transition-all"
            >
              Try Without Login →
            </Link>
          </div>

          {/* Stats */}
          <div className="mt-20 grid grid-cols-3 gap-8 max-w-3xl mx-auto">
            <div>
              <div className="text-4xl font-bold text-gray-900">10K+</div>
              <div className="text-gray-600 mt-2">Articles Analyzed</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-gray-900">95%</div>
              <div className="text-gray-600 mt-2">Accuracy</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-gray-900">&lt;2s</div>
              <div className="text-gray-600 mt-2">Response Time</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-600">
              Everything you need for comprehensive news analysis
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { color: 'blue', title: 'Real-time Analysis', desc: 'Get instant sentiment analysis on the latest news articles from multiple sources.', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
              { color: 'purple', title: 'Visual Analytics', desc: 'Beautiful charts and graphs to understand sentiment trends at a glance.', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
              { color: 'green', title: 'AI Summaries', desc: 'Get concise AI-generated summaries of lengthy articles and comment sections.', icon: 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01' },
              { color: 'orange', title: 'Multi-Source', desc: 'Analyze news from Naver, Google, and other major news platforms.', icon: 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4' },
              { color: 'red', title: 'Export Data', desc: 'Download your analysis results in CSV or JSON format for further processing.', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
              { color: 'indigo', title: 'Search History', desc: 'Keep track of your searches and revisit past analysis results anytime.', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
            ].map((feature, i) => (
              <div key={i} className="bg-white p-8 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                <div className={`w-12 h-12 bg-${feature.color}-100 rounded-xl flex items-center justify-center mb-4`}>
                  <svg className={`w-6 h-6 text-${feature.color}-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={feature.icon} />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-600">
              Start free, upgrade when you need more
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Free Plan */}
            <div className="bg-white border-2 border-gray-200 rounded-2xl p-8 hover:border-gray-300 transition-colors">
              <div className="text-center">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Free</h3>
                <div className="text-5xl font-bold text-gray-900 mb-1">$0</div>
                <p className="text-gray-600 mb-8">Perfect to get started</p>
              </div>

              <ul className="space-y-4 mb-8">
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-green-500 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-600">Up to <strong>3 articles</strong> per search</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-green-500 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-600">Basic sentiment analysis</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-gray-300 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span className="text-gray-400">No search history</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-6 h-6 text-gray-300 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span className="text-gray-400">No data export</span>
                </li>
              </ul>

              <Link
                href="/dashboard"
                className="block w-full text-center bg-gray-100 text-gray-900 px-6 py-3 rounded-full font-medium hover:bg-gray-200 transition-colors"
              >
                Try Now
              </Link>
            </div>

            {/* Premium Plan */}
            <div className="bg-gray-900 text-white rounded-2xl p-8 relative shadow-xl">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                  POPULAR
                </span>
              </div>

              <div className="text-center">
                <h3 className="text-2xl font-bold mb-2">Premium</h3>
                <div className="text-5xl font-bold mb-1">Free</div>
                <p className="text-gray-400 mb-8">For power users</p>
              </div>

              <ul className="space-y-4 mb-8">
                {[
                  'Up to 50 articles per search',
                  'Advanced AI analysis & summaries',
                  'Search history & saved results',
                  'Export to CSV/JSON',
                  'Priority support'
                ].map((item, i) => (
                  <li key={i} className="flex items-start">
                    <svg className="w-6 h-6 text-green-400 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span dangerouslySetInnerHTML={{ __html: item.includes('50') ? item.replace('50', '<strong>50</strong>') : item }} />
                  </li>
                ))}
              </ul>

              <Link
                href="/auth/register"
                className="block w-full text-center bg-white text-gray-900 px-6 py-3 rounded-full font-medium hover:bg-gray-100 transition-colors"
              >
                Sign Up Free
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gray-900 text-white">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to get started?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Join thousands of users analyzing news sentiment with AI
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/auth/register"
              className="bg-white text-gray-900 px-8 py-4 rounded-full text-lg font-medium hover:bg-gray-100 transition-all hover:scale-105"
            >
              Create Free Account
            </Link>
            <Link
              href="/dashboard"
              className="border-2 border-white text-white px-8 py-4 rounded-full text-lg font-medium hover:bg-white hover:text-gray-900 transition-all"
            >
              Try Without Signing Up
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="text-2xl font-bold text-gray-900 mb-4">NewsAI</div>
              <p className="text-gray-600 text-sm">
                AI-powered news sentiment analysis platform.
              </p>
            </div>
            <div>
              <h4 className="font-bold text-gray-900 mb-4">Product</h4>
              <ul className="space-y-2 text-gray-600 text-sm">
                <li><Link href="#features" className="hover:text-gray-900">Features</Link></li>
                <li><Link href="#pricing" className="hover:text-gray-900">Pricing</Link></li>
                <li><Link href="/dashboard" className="hover:text-gray-900">Dashboard</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-gray-900 mb-4">Company</h4>
              <ul className="space-y-2 text-gray-600 text-sm">
                <li><a href="#" className="hover:text-gray-900">About</a></li>
                <li><a href="#" className="hover:text-gray-900">Blog</a></li>
                <li><a href="#" className="hover:text-gray-900">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-gray-900 mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-600 text-sm">
                <li><a href="#" className="hover:text-gray-900">Privacy</a></li>
                <li><a href="#" className="hover:text-gray-900">Terms</a></li>
                <li><a href="#" className="hover:text-gray-900">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 border-t border-gray-100 text-center text-gray-600 text-sm">
            © 2024 NewsAI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
