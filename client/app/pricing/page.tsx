'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Check } from 'lucide-react';
import { motion } from 'framer-motion';

export default function PricingPage() {
  const formats = [
    {
      name: 'Digital Copy',
      price: 999,
      description: 'Perfect for instant reading',
      features: [
        'Instant PDF download',
        'Read on any device',
        'High-quality illustrations',
        'Printable at home',
        'Lifetime access',
      ],
      color: 'from-violet-400 to-violet-600',
    },
    {
      name: 'Softcover',
      price: 1599,
      description: 'Beautiful printed book',
      features: [
        'Professional softcover binding',
        'Premium paper quality',
        'Vibrant color printing',
        'Ships in 5-7 business days',
        'Free digital copy included',
      ],
      color: 'from-[#6B21A8] to-[#9333EA]',
      popular: true,
    },
    {
      name: 'Hardcover',
      price: 1999,
      description: 'Premium keepsake edition',
      features: [
        'Durable hardcover binding',
        'Premium thick pages',
        'Glossy finish cover',
        'Perfect for gifting',
        'Free digital copy included',
      ],
      color: 'from-[#C9A227] to-[#F59E0B]',
    },
  ];

  return (
    <div className="min-h-screen relative">
      <main className="relative z-10 container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="max-w-6xl mx-auto"
        >
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
              Choose Your Format
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Select the perfect format for your personalized book. All formats include the same magical story featuring your child.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {formats.map((format, index) => (
              <motion.div
                key={format.name}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card
                  className={`rounded-3xl shadow-lg hover:shadow-xl transition relative ${
                    format.popular ? 'border-2 border-primary' : ''
                  }`}
                >
                  {format.popular && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <span className="bg-primary text-primary-foreground px-4 py-1 rounded-full text-sm font-semibold">
                        Most Popular
                      </span>
                    </div>
                  )}

                  <CardHeader className="text-center pb-4">
                    <div
                      className={`w-28 h-28 mx-auto rounded-full bg-gradient-to-br ${format.color} flex items-center justify-center mb-4`}
                    >
                      <span className="text-2xl font-bold text-white">
                        ₹{format.price}
                      </span>
                    </div>
                    <CardTitle className="text-2xl">{format.name}</CardTitle>
                    <p className="text-muted-foreground">{format.description}</p>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <ul className="space-y-3">
                      {format.features.map((feature) => (
                        <li key={feature} className="flex items-start">
                          <Check className="h-5 w-5 text-primary mr-2 flex-shrink-0 mt-0.5" />
                          <span className="text-sm">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <Link href="/coloring-books" className="block">
                      <Button
                        className={`w-full rounded-xl ${
                          format.popular ? '' : 'bg-secondary hover:bg-secondary/80 text-secondary-foreground'
                        }`}
                      >
                        Get Started
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
            viewport={{ once: true }}
            className="mt-16"
          >
            <Card className="rounded-3xl shadow-lg p-8 bg-gradient-to-br from-purple-50 to-amber-50 border border-purple-100">
              <h2 className="text-3xl font-bold mb-6 text-center">
                Frequently Asked Questions
              </h2>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold mb-2">How long does shipping take?</h3>
                  <p className="text-sm text-muted-foreground">
                    Softcover books ship in 5-7 business days, while hardcover books take 7-10 business days. Digital copies are available instantly.
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Can I order multiple copies?</h3>
                  <p className="text-sm text-muted-foreground">
                    Yes! You can reorder any book from your dashboard at any time. Perfect for sharing with family and friends.
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">What age groups are available?</h3>
                  <p className="text-sm text-muted-foreground">
                    We offer books for ages 3-5, 6-8, and 9-12, with content tailored to each age group's reading level.
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Is there a satisfaction guarantee?</h3>
                  <p className="text-sm text-muted-foreground">
                    Absolutely! If you're not completely satisfied with your book, contact us within 30 days for a full refund.
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        </motion.div>
      </main>
    </div>
  );
}
