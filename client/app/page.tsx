'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Sparkles, Palette, Heart, Star } from 'lucide-react';
import { motion } from 'framer-motion';

export default function HomePage() {
  return (
    <div className="min-h-screen relative">
      <main className="relative z-10">
        <section className="container mx-auto px-4 py-20 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="flex justify-center mb-6">
              <Sparkles className="h-16 w-16 text-primary sparkle" />
            </div>
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-[#6B21A8] via-[#9333EA] to-[#C9A227] bg-clip-text text-transparent">
              Where Every Child
              <br />
              Becomes the Hero
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Create magical personalized coloring books featuring your child as the star of their own adventure
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <Link href="/coloring-books">
                <Button size="lg" className="text-lg px-8 py-6 rounded-2xl shadow-lg hover:shadow-xl transition-all bg-[#6B21A8] hover:bg-[#581C87]">
                  <Palette className="mr-2 h-5 w-5" />
                  Browse Coloring Books
                </Button>
              </Link>
            </div>
          </motion.div>
        </section>

        <section className="container mx-auto px-4 py-16">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
            viewport={{ once: true }}
            className="grid md:grid-cols-3 gap-8"
          >
            <Card className="border-2 border-purple-200 shadow-lg hover:shadow-xl transition-all rounded-3xl overflow-hidden">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-4">
                  <Heart className="h-8 w-8 text-[#6B21A8]" />
                </div>
                <h3 className="text-2xl font-bold mb-3">Personalized</h3>
                <p className="text-muted-foreground">
                  Your child becomes the hero in beautifully illustrated stories tailored just for them
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-amber-200 shadow-lg hover:shadow-xl transition-all rounded-3xl overflow-hidden">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center mx-auto mb-4">
                  <Star className="h-8 w-8 text-[#C9A227]" />
                </div>
                <h3 className="text-2xl font-bold mb-3">High Quality</h3>
                <p className="text-muted-foreground">
                  Professional illustrations and printing that will last for years to come
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-violet-200 shadow-lg hover:shadow-xl transition-all rounded-3xl overflow-hidden">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 rounded-full bg-violet-100 flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="h-8 w-8 text-[#7C3AED]" />
                </div>
                <h3 className="text-2xl font-bold mb-3">Magical</h3>
                <p className="text-muted-foreground">
                  Watch their face light up as they discover themselves in magical adventures
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </section>

        <section className="container mx-auto px-4 py-16 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            viewport={{ once: true }}
            className="bg-gradient-to-r from-purple-100 via-violet-50 to-amber-50 rounded-3xl p-12 shadow-xl border border-purple-100"
          >
            <h2 className="text-4xl font-bold mb-4 text-[#6B21A8]">Ready to Create Magic?</h2>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Start creating personalized books that your child will treasure forever
            </p>
            <Link href="/coloring-books">
              <Button size="lg" className="text-lg px-8 py-6 rounded-2xl bg-[#6B21A8] hover:bg-[#581C87]">
                Get Started Now
              </Button>
            </Link>
          </motion.div>
        </section>
      </main>

      <footer className="relative z-10 border-t mt-20 py-8 bg-white/60 backdrop-blur">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>&copy; 2026 Pandora Pages. Crafted for you, one page at a time.</p>
        </div>
      </footer>
    </div>
  );
}
