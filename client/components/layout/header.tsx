'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/providers/auth-provider';
import { BookOpen, User, LogOut } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';


const navLinks = [
  { href: '/coloring-books', label: 'Coloring Books' },
  { href: '/story-books', label: 'Story Books' },
  { href: '/about', label: 'About' },
];

export function Header() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <Image
            src="/logo_without_name.jpeg"
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

        <div className="flex items-center gap-4 min-w-[120px] justify-end">
          {isLoading ? (
            <div className="h-9 w-24 rounded-md bg-muted animate-pulse" />
          ) : isAuthenticated && user ? (
            <>
              <Link href="/dashboard" prefetch={true}>
                <Button variant="outline" size="sm" className="hidden sm:flex border-primary/30 text-primary hover:bg-primary/5">
                  <BookOpen className="h-4 w-4 mr-2" />
                  My Books
                </Button>
              </Link>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-9 w-9 rounded-full p-0">
                    <Avatar className="h-9 w-9">
                      <AvatarImage src={user.avatar} alt={user.name} />
                      <AvatarFallback>
                        <User className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem asChild>
                    <Link href="/dashboard" className="cursor-pointer">
                      <BookOpen className="h-4 w-4 mr-2" />
                      Dashboard
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={logout} className="cursor-pointer">
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <Link href="/login" prefetch={true}>
              <Button size="sm" className="bg-primary hover:bg-primary/90">
                Sign In
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
