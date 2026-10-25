'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { FEATURE_ITEMS } from '@/lib/features';
import { useAuth } from '@/hooks/useAuth';
import UserMenu from '@/components/auth/UserMenu';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [featuresOpen, setFeaturesOpen] = useState(false);
  const [mobileFeaturesOpen, setMobileFeaturesOpen] = useState(false);
  const [prevScrollPos, setPrevScrollPos] = useState(0);
  const [visible, setVisible] = useState(true);
  const dropdownRef = useRef(null);
  const pathname = usePathname();
  const { isAuthenticated, loading: authLoading } = useAuth();

  useEffect(() => {
    setIsOpen(false);
    setFeaturesOpen(false);
    setMobileFeaturesOpen(false);
  }, [pathname]);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollPos = window.scrollY;
      setVisible(currentScrollPos < prevScrollPos || currentScrollPos < 80);
      setPrevScrollPos(currentScrollPos);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [prevScrollPos]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setFeaturesOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isFeatureActive = FEATURE_ITEMS.some(
    (f) => pathname === f.href || pathname.startsWith(f.href + '/')
  );

  const authButtons = authLoading ? (
    <span className="w-20 h-9 rounded-lg bg-[#EAE3D2]/50 animate-pulse" aria-hidden />
  ) : isAuthenticated ? (
    <UserMenu />
  ) : (
    <>
      <Link
        href="/login"
        className="px-4 py-2 text-sm font-bold text-[#1E2229]/80 hover:text-[#C85A32] transition-colors"
      >
        Login
      </Link>
      <Link
        href="/signup"
        className="px-4 py-2 border border-[#C85A32] rounded-lg text-sm font-bold text-[#C85A32] hover:bg-[#C85A32] hover:text-white transition-all shadow-sm"
      >
        Sign Up
      </Link>
    </>
  );

  return (
    <nav
      className={`fixed top-5 left-0 right-0 mx-auto max-w-6xl bg-[#FFFFFF]/95 text-[#1E2229] px-6 py-4 rounded-xl border border-[#EAE3D2] shadow-[0_10px_30px_-10px_rgba(30,34,41,0.08)] z-50 transform transition-all duration-300 ease-in-out ${
        visible ? 'translate-y-0' : '-translate-y-full'
      }`}
    >
      <div className="max-w-7xl mx-auto flex justify-between items-center h-full">
        <motion.div
          className="text-2xl font-extrabold tracking-widest font-display text-[#1E3F2E]"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Link href="/" className="hover:opacity-85 flex items-center gap-2">
            <span className="text-xl">🧭</span> AINOMAD
          </Link>
        </motion.div>

        <div className="hidden md:flex space-x-6 items-center">
          <div className="relative" ref={dropdownRef}>
            <button
              type="button"
              onClick={() => setFeaturesOpen(!featuresOpen)}
              className={`text-sm font-semibold tracking-wide flex items-center gap-1 transition-colors ${
                isFeatureActive ? 'text-[#C85A32]' : 'text-[#1E2229]/80 hover:text-[#C85A32]'
              }`}
              aria-expanded={featuresOpen}
              aria-haspopup="true"
            >
              Features
              <ChevronDown
                size={16}
                className={`transition-transform ${featuresOpen ? 'rotate-180' : ''}`}
              />
            </button>

            <AnimatePresence>
              {featuresOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.15 }}
                  className="absolute top-full left-0 mt-2 w-72 bg-white border border-[#EAE3D2] rounded-xl shadow-lg py-2 max-h-[70vh] overflow-y-auto"
                >
                  {FEATURE_ITEMS.map((item) => (
                    <Link
                      key={item.slug}
                      href={item.href}
                      className="block px-4 py-2.5 text-sm text-[#1E2229]/85 hover:bg-[#FBF9F6] hover:text-[#C85A32] transition-colors"
                    >
                      {item.title}
                    </Link>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <Link
            href="/about"
            className="text-sm font-semibold tracking-wide text-[#1E2229]/80 hover:text-[#C85A32] transition-colors"
          >
            About
          </Link>
          <Link
            href="/contact"
            className="text-sm font-semibold tracking-wide text-[#1E2229]/80 hover:text-[#C85A32] transition-colors"
          >
            Contact
          </Link>
          <div className="flex items-center gap-2">{authButtons}</div>
        </div>

        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="block md:hidden focus:outline-none text-[#1E2229] hover:text-[#C85A32]"
          aria-label="Toggle menu"
        >
          <div className="space-y-1.5">
            <span className="block w-6 h-0.5 bg-current" />
            <span className="block w-6 h-0.5 bg-current" />
            <span className="block w-6 h-0.5 bg-current" />
          </div>
        </button>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="md:hidden mt-4 pt-4 border-t border-[#EAE3D2] space-y-2"
          >
            <button
              type="button"
              onClick={() => setMobileFeaturesOpen(!mobileFeaturesOpen)}
              className="w-full flex items-center justify-center gap-1 py-2 text-sm font-semibold text-[#1E2229] hover:bg-[#F9F6F0] rounded"
            >
              Features
              <ChevronDown
                size={16}
                className={`transition-transform ${mobileFeaturesOpen ? 'rotate-180' : ''}`}
              />
            </button>
            {mobileFeaturesOpen && (
              <div className="pl-3 space-y-1 border-l-2 border-[#EAE3D2] ml-4 mb-2">
                {FEATURE_ITEMS.map((item) => (
                  <Link
                    key={item.slug}
                    href={item.href}
                    className="block py-2 text-xs font-semibold text-[#1E2229]/80 hover:text-[#C85A32]"
                  >
                    {item.title}
                  </Link>
                ))}
              </div>
            )}
            <Link
              href="/about"
              className="block text-center py-2 text-sm font-semibold text-[#1E2229] hover:bg-[#F9F6F0] rounded"
            >
              About
            </Link>
            <Link
              href="/contact"
              className="block text-center py-2 text-sm font-semibold text-[#1E2229] hover:bg-[#F9F6F0] rounded"
            >
              Contact
            </Link>
            <div className="flex flex-col gap-2 pt-2">
              {authLoading ? (
                <div className="h-10 rounded-lg bg-[#EAE3D2]/50 animate-pulse" />
              ) : isAuthenticated ? (
                <div className="flex justify-center">
                  <UserMenu />
                </div>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="w-full text-center py-2 text-sm font-bold text-[#1E2229] hover:bg-[#F9F6F0] rounded"
                  >
                    Login
                  </Link>
                  <Link
                    href="/signup"
                    className="w-full text-center py-2 border border-[#C85A32] rounded-lg text-sm font-bold text-[#C85A32] hover:bg-[#C85A32] hover:text-white"
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
