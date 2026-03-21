import Link from 'next/link';
import Image from 'next/image';
import { Instagram, Mail, Heart } from 'lucide-react';

const SECTIONS = [
  {
    heading: 'Books',
    links: [
      { label: 'Coloring Books', href: '/coloring-books' },
      { label: 'Story Books', href: '/story-books' },
    ],
  },
  {
    heading: 'Account',
    links: [
      { label: 'Sign Up', href: '/signup' },
      { label: 'Log In', href: '/login' },
      { label: 'Dashboard', href: '/dashboard' },
    ],
  },
  {
    heading: 'Company',
    links: [
      { label: 'About Us', href: '/about' },
      { label: 'Contact', href: 'mailto:hello@pandorapages.in' },
      { label: 'Privacy Policy', href: '/privacy' },
      { label: 'Terms of Service', href: '/terms' },
    ],
  },
];

export function Footer() {
  return (
    <footer className="relative z-10 border-t mt-20 bg-white/80 backdrop-blur">
      {/* Main grid */}
      <div className="container mx-auto px-4 py-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
        {/* Brand column */}
        <div className="flex flex-col gap-4">
          <Link href="/" className="flex items-center gap-2 w-fit">
            <Image
              src="/logo_without_name.jpeg"
              alt="Pandora Pages logo"
              width={44}
              height={44}
              className="object-contain rounded-lg"
            />
            <div className="leading-tight">
              <p className="text-base font-bold text-[#6B21A8] tracking-wide">Pandora Pages</p>
              <p className="text-[10px] font-medium text-[#C9A227] uppercase tracking-widest">
                crafted for you
              </p>
            </div>
          </Link>
          <p className="text-sm text-muted-foreground max-w-xs">
            Personalised books where every child is the hero — coloring adventures and illustrated
            stories made just for them.
          </p>
          {/* Social */}
          <div className="flex items-center gap-3 mt-1">
            <Link
              href="https://www.instagram.com/pandorapages.in/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-pink-500 transition-colors"
              aria-label="Follow Pandora Pages on Instagram"
            >
              <Instagram className="h-4 w-4" />
              <span>@pandorapages.in</span>
            </Link>
          </div>
          <Link
            href="mailto:hello@pandorapages.in"
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-[#6B21A8] transition-colors w-fit"
          >
            <Mail className="h-4 w-4" />
            hello@pandorapages.in
          </Link>
        </div>

        {/* Nav sections */}
        {SECTIONS.map((section) => (
          <div key={section.heading}>
            <h4 className="text-sm font-semibold text-foreground mb-3 uppercase tracking-wider">
              {section.heading}
            </h4>
            <ul className="space-y-2">
              {section.links.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-[#6B21A8] transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Bottom bar */}
      <div className="border-t">
        <div className="container mx-auto px-4 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
          <p>&copy; {new Date().getFullYear()} Pandora Pages. All rights reserved.</p>
          <p className="flex items-center gap-1">
            Made with <Heart className="h-3 w-3 text-pink-500 fill-pink-500" /> for little adventurers
          </p>
        </div>
      </div>
    </footer>
  );
}

