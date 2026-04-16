'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Loader2, Palette, Sparkles } from 'lucide-react';

import { DigitalBookCard } from '@/features/digital-books/components/digital-book-card';
import { DigitalBookFiltersBar } from '@/features/digital-books/components/digital-book-filters';
import {
  useDigitalBookFilterOptions,
  useDigitalBooks,
} from '@/features/digital-books/hooks/useDigitalBooks';
import { DigitalBookFilters } from '@/features/digital-books/types/digital-book.types';

const CONTAINER = 'container mx-auto px-4';

export default function DigitalBooksPage() {
  const [filters, setFilters] = useState<DigitalBookFilters>({});
  const { data: books = [], isLoading, isError } = useDigitalBooks(filters);
  const { data: filterOptions } = useDigitalBookFilterOptions();

  return (
    <div className="fixed inset-x-0 top-16 bottom-0 flex flex-col overflow-hidden bg-[#f7f8fc]">

      {/* Hero */}
      <div className="relative shrink-0 overflow-hidden bg-gradient-to-r from-[#1a1f6e] via-[#2d35a8] to-[#4f46e5] text-white">
        <div className="pointer-events-none absolute -right-16 -top-16 h-72 w-72 rounded-full bg-white/5" />
        <div className="pointer-events-none absolute -bottom-10 right-40 h-48 w-48 rounded-full bg-white/5" />
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className={`${CONTAINER} py-8`}
        >
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/10 px-3 py-1 text-xs font-medium">
                <Sparkles className="h-3.5 w-3.5 text-yellow-300" />
                Personalized for every child
              </div>
              <h1 className="text-4xl font-extrabold uppercase leading-tight tracking-tight md:text-5xl">
                Digital Books <span className="text-yellow-300">@ &#x20b9;99</span>
              </h1>
              <p className="mt-2 max-w-lg text-sm text-indigo-200 md:text-base">
                Story &amp; drawing books in stunning genres &mdash; sent directly to your email.
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <div className="flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2 text-sm">
                  <BookOpen className="h-4 w-4 text-blue-300" /> Story Books
                </div>
                <div className="flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2 text-sm">
                  <Palette className="h-4 w-4 text-pink-300" /> Drawing Books
                </div>
              </div>
            </div>
            <div className="shrink-0 text-center">
              <div className="rounded-2xl border border-white/20 bg-white/10 px-8 py-5">
                <p className="text-5xl font-black text-yellow-300">&#x20b9;99</p>
                <p className="mt-1 text-xs text-indigo-300">flat per book</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Filter bar */}
      <div className={`${CONTAINER} shrink-0 py-4`}>
        <DigitalBookFiltersBar value={filters} options={filterOptions} onChange={setFilters} />
      </div>

      {/* Cards - only this scrolls */}
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className={`${CONTAINER} pb-8`}>
          {isLoading ? (
            <div className="flex min-h-[300px] items-center justify-center gap-3 rounded-2xl bg-white shadow-sm">
              <Loader2 className="h-5 w-5 animate-spin text-indigo-600" />
              <span className="text-sm text-slate-500">Loading digital books...</span>
            </div>
          ) : isError ? (
            <div className="rounded-2xl border border-red-100 bg-red-50 p-8 text-center text-sm text-red-700">
              Unable to fetch digital books right now. Please try again in a moment.
            </div>
          ) : books.length === 0 ? (
            <div className="rounded-2xl bg-white p-12 text-center shadow-sm">
              <p className="text-4xl">&#x1f4da;</p>
              <h2 className="mt-3 text-lg font-semibold text-slate-900">No books found</h2>
              <p className="mt-1 text-sm text-slate-500">Try adjusting your search or filters.</p>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5"
            >
              {books.map((book) => (
                <DigitalBookCard key={book.id} book={book} />
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
