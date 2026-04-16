import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, BookOpen, Download, Globe, Palette, Star } from 'lucide-react';
import { useState } from 'react';

import { DigitalBook } from '@/features/digital-books/types/digital-book.types';

interface DigitalBookCardProps {
  book: DigitalBook;
}

export function DigitalBookCard({ book }: DigitalBookCardProps) {
  const fallbackCover = '/logo_without_name.png';
  const initialCover = book.coverImagePresignedUrl || fallbackCover;
  const [imgSrc, setImgSrc] = useState(initialCover);
  const isStory = book.bookType === 'story';
  const rating = Number.isFinite(book.rating) ? book.rating.toFixed(1) : '0.0';
  const language = book.language ? book.language.charAt(0).toUpperCase() + book.language.slice(1) : 'English';
  const pages = book.totalPages ? `${book.totalPages} pages` : 'PDF format';

  return (
    <motion.div
      whileHover={{ y: -6, scale: 1.01 }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      className="group mx-auto w-full max-w-[200px]"
    >
      <Link href={`/digital-books/${book.id}`} className="block">
        <div className="overflow-hidden rounded-2xl bg-gradient-to-b from-white to-slate-50 shadow-md ring-1 ring-slate-200/70 transition-all group-hover:-translate-y-0.5 group-hover:shadow-xl group-hover:ring-blue-200">
          {/* Cover image */}
          <div className="relative h-[220px] w-full overflow-hidden rounded-t-2xl bg-gradient-to-br from-blue-50 to-indigo-100">
            <img
              src={imgSrc}
              alt={book.bookName}
              loading="lazy"
              className="h-full w-full object-contain object-center bg-white p-1 transition-transform duration-500 group-hover:scale-105"
              onError={() => {
                if (imgSrc !== fallbackCover) {
                  setImgSrc(fallbackCover);
                }
              }}
            />
          </div>

          {/* Title + metadata rows */}
          <div className="px-3 py-2.5">
            <p className="line-clamp-1 text-sm font-semibold uppercase tracking-wide text-slate-900">{book.bookName}</p>

            <div className="mt-1 flex items-center justify-between">
              <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${isStory ? 'bg-violet-100 text-violet-700' : 'bg-orange-100 text-orange-700'}`}>
                {isStory ? <BookOpen className="h-3 w-3" /> : <Palette className="h-3 w-3" />}
                {isStory ? 'Story' : 'Drawing'}
              </span>
              <span className="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
                ₹{Math.round(book.price ?? 99)}
              </span>
            </div>

            <div className="mt-1 flex items-center justify-between">
              <span className="text-[10px] text-slate-500">{book.genreName || 'General'}</span>
              <span className="flex items-center gap-1 text-[10px] font-semibold text-blue-600 transition-colors group-hover:text-blue-700">
                View <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
              </span>
            </div>

            <div className="mt-2 grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] text-slate-600">
              <span className="inline-flex items-center gap-1">
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> {rating}
              </span>
              <span className="inline-flex items-center justify-end gap-1">
                <Globe className="h-3 w-3 text-slate-500" /> {language}
              </span>
              <span>{pages}</span>
              <span className="inline-flex items-center justify-end gap-1">
                <Download className="h-3 w-3 text-slate-500" /> {book.downloadCount}
              </span>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
