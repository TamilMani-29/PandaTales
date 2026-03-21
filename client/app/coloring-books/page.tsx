'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Camera, Palette, Sparkles, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { Footer } from '@/components/layout/footer';

const creationModes = [
  {
    href: '/coloring-books/create?mode=photo',
    icon: Camera,
    title: 'Photo to Coloring Pages',
    subtitle: 'Upload up to 10 photos',
    description:
      'Upload photos of your child, family, or pets. We convert each photo into a beautiful hand-drawn style coloring page — a unique book made entirely from your memories.',
    badge: 'Up to 10 pages',
    iconBg: 'bg-violet-100',
    iconColor: 'text-[#6B21A8]',
    badgeBg: 'bg-violet-100 text-violet-700',
    borderHover: 'hover:border-violet-400',
    accentBar: 'bg-[#6B21A8]',
    steps: ['Upload up to 10 photos', 'We trace each photo into line art', 'Get a printable coloring book'],
  },
  {
    href: '/coloring-books/create?mode=theme',
    icon: Palette,
    title: 'Theme-Based Coloring Book',
    subtitle: 'Choose a theme, set page count',
    description:
      'Pick from 10 magical themes — Space, Jungle, Princess and more. Choose how many pages you want (8 to 32). Optionally add reference photos to weave your child\'s likeness into the illustrations.',
    badge: '8–32 pages',
    iconBg: 'bg-amber-50',
    iconColor: 'text-[#C9A227]',
    badgeBg: 'bg-amber-100 text-amber-700',
    borderHover: 'hover:border-amber-400',
    accentBar: 'bg-[#C9A227]',
    steps: ['Select a theme (10 options)', 'Choose page count (8–32)', 'Optionally add reference photos'],
  },
];

export default function ColoringBooksPage() {
  return (
    <div className="min-h-screen relative">
      <main className="relative z-10">
        <section className="container mx-auto px-4 pt-12 pb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="text-center mb-12"
          >
            <div className="inline-flex items-center gap-2 bg-purple-100 text-[#6B21A8] text-sm font-semibold px-4 py-1.5 rounded-full mb-4">
              <Sparkles className="h-4 w-4" />
              Personalized Coloring Books
            </div>
            <h1 className="text-4xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
              Color Your World
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Two magical ways to create a coloring book your child will absolutely love
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {creationModes.map((mode, i) => {
              const Icon = mode.icon;
              return (
                <motion.div
                  key={mode.href}
                  initial={{ opacity: 0, y: 24 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2, delay: i * 0.12 }}
                  whileHover={{ y: -4 }}
                >
                  <Card className={`h-full rounded-3xl shadow-lg border-2 border-border ${mode.borderHover} transition-all overflow-hidden group`}>
                    <div className={`h-1.5 w-full ${mode.accentBar}`} />
                    <CardContent className="p-8 flex flex-col h-full">
                      <div className="flex items-start justify-between mb-5">
                        <div className={`w-16 h-16 rounded-2xl ${mode.iconBg} flex items-center justify-center`}>
                          <Icon className={`h-8 w-8 ${mode.iconColor}`} />
                        </div>
                        <span className={`text-xs font-semibold px-3 py-1 rounded-full ${mode.badgeBg}`}>
                          {mode.badge}
                        </span>
                      </div>

                      <h2 className="text-2xl font-bold mb-1">{mode.title}</h2>
                      <p className="text-sm font-semibold text-[#6B21A8] mb-3">{mode.subtitle}</p>
                      <p className="text-muted-foreground text-sm leading-relaxed mb-6 flex-1">
                        {mode.description}
                      </p>

                      <div className="space-y-2 mb-7">
                        {mode.steps.map((step, j) => (
                          <div key={j} className="flex items-center gap-2.5 text-sm">
                            <div className={`w-5 h-5 rounded-full ${mode.accentBar} flex items-center justify-center flex-shrink-0`}>
                              <span className="text-white text-[10px] font-bold">{j + 1}</span>
                            </div>
                            <span className="text-muted-foreground">{step}</span>
                          </div>
                        ))}
                      </div>

                      <Link href={mode.href}>
                        <Button className="w-full rounded-xl bg-[#6B21A8] hover:bg-[#581C87] group-hover:shadow-md transition-shadow">
                          Get Started
                          <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                        </Button>
                      </Link>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </section>

        <section className="container mx-auto px-4 py-12">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.2 }}
            className="max-w-3xl mx-auto bg-gradient-to-br from-purple-100 via-violet-50 to-amber-50 rounded-3xl p-10 text-center border border-purple-100 shadow-lg"
          >
            <Sparkles className="h-10 w-10 mx-auto mb-4 text-[#6B21A8] sparkle" />
            <h2 className="text-3xl font-bold mb-3 text-[#6B21A8]">Not sure which to choose?</h2>
            <p className="text-muted-foreground mb-6 leading-relaxed">
              <strong>Photo mode</strong> is great when you have special photos you'd love to see as art.{' '}
              <strong>Theme mode</strong> is perfect when you want a complete story-driven book around your child's favourite world.
            </p>
            <Link href="/coloring-books/create?mode=photo">
              <Button size="lg" className="rounded-2xl px-8 bg-[#6B21A8] hover:bg-[#581C87]">
                <Sparkles className="mr-2 h-5 w-5" />
                Start Creating
              </Button>
            </Link>
          </motion.div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
