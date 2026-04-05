'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Menu, X } from 'lucide-react';
// AUTH: import { Button } from '@/components/ui/button';
// AUTH: import { useAuth } from '@/lib/providers/auth-provider';
// AUTH: import { BookOpen, User, LogOut } from 'lucide-react';
// AUTH: import {
// AUTH:   DropdownMenu,
// AUTH:   DropdownMenuContent,
// AUTH:   DropdownMenuItem,
// AUTH:   DropdownMenuTrigger,
// AUTH: } from '@/components/ui/dropdown-menu';
// AUTH: import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';


const navLinks = [
  { href: '/coloring-books', label: 'Coloring Books' },
  { href: '/story-books', label: 'Story Books' },
  { href: '/about', label: 'About' },
];

export function Header() {
  // AUTH: const { user, isAuthenticated, isLoading, logout } = useAuth();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity" onClick={() => setMobileOpen(false)}>
          <Image
            src="/logo_without_name.png"
            alt="Pandora Pages Logo"
            width={52}
            height={52}
            className="object-contain"
          />
          <div className="flex flex-col leading-tight">
            <span className="text-xl font-bold text-[#6B21A8] tracking-wide">
              Pandora Pages
            </span>
            <span className="text-[10px] font-medium text-[#C9A227] uppercase tracking-widest -mt-0.5">
              crafted for you
            </span>
          </div>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6">
          {navLinks.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              prefetch={true}
              className={`text-sm font-medium transition-colors hover:text-primary ${
                pathname === href ? 'text-primary font-semibold' : 'text-muted-foreground'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Mobile hamburger */}
        <button
          className="md:hidden flex items-center justify-center rounded-lg p-2 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          onClick={() => setMobileOpen((v) => !v)}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>

        {/* AUTH: Sign in / user menu — re-enable when authentication is introduced */}
      </div>

      {/* Mobile nav panel */}
      {mobileOpen && (
        <div className="md:hidden border-t bg-white/95 backdrop-blur px-4 py-3 space-y-1">
          {navLinks.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              prefetch={true}
              onClick={() => setMobileOpen(false)}
              className={`block py-2.5 px-3 rounded-xl text-sm font-medium transition-colors ${
                pathname === href
                  ? 'text-primary font-semibold bg-primary/5'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              }`}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </header>
  );
}
