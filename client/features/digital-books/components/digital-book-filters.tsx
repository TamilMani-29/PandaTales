'use client';

import { Search } from 'lucide-react';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DigitalBookFilterOptions, DigitalBookFilters } from '@/features/digital-books/types/digital-book.types';

const STATIC_GENRES = [
  'Adventure', 'Fantasy', 'Animals', 'Space', 'Ocean', 'Jungle',
  'Fairy Tale', 'Science', 'Superheroes', 'Friendship',
];

const STATIC_STYLES = ['animation', 'illustration'] as const;

interface DigitalBookFiltersProps {
  value: DigitalBookFilters;
  options?: DigitalBookFilterOptions;
  onChange: (next: DigitalBookFilters) => void;
}

export function DigitalBookFiltersBar({ value, options, onChange }: DigitalBookFiltersProps) {
  const update = <K extends keyof DigitalBookFilters>(key: K, nextValue: DigitalBookFilters[K] | undefined) => {
    onChange({ ...value, [key]: nextValue });
  };

  const genres = options?.genres?.length ? options.genres : STATIC_GENRES;
  const styles = options?.styles?.length ? options.styles : STATIC_STYLES;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="flex items-center h-14 divide-x divide-slate-200">
        {/* Search — takes remaining space */}
        <div className="relative flex-1 min-w-0 h-full flex items-center">
          <Search className="pointer-events-none absolute left-5 h-4 w-4 text-slate-400 shrink-0" />
          <input
            value={value.search || ''}
            onChange={(e) => update('search', e.target.value || undefined)}
            placeholder="Search by title, genre or style..."
            className="h-full w-full bg-transparent pl-12 pr-4 text-sm outline-none placeholder:text-slate-400 truncate"
          />
        </div>

        {/* Book Type */}
        <div className="w-[148px] shrink-0 h-full">
          <Select value={value.bookType || 'all'} onValueChange={(next) => update('bookType', next === 'all' ? undefined : (next as DigitalBookFilters['bookType']))}>
            <SelectTrigger className="h-full w-full rounded-none border-0 bg-transparent px-4 text-sm shadow-none ring-0 focus:ring-0 focus:ring-offset-0">
              <SelectValue placeholder="Book Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="story">📖 Story</SelectItem>
              <SelectItem value="coloring">🎨 Drawing</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Genre */}
        <div className="w-[160px] shrink-0 h-full">
          <Select value={value.genre || 'all'} onValueChange={(next) => update('genre', next === 'all' ? undefined : next)}>
            <SelectTrigger className="h-full w-full rounded-none border-0 bg-transparent px-4 text-sm shadow-none ring-0 focus:ring-0 focus:ring-offset-0">
              <SelectValue placeholder="Genre" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Genres</SelectItem>
              {genres.map((genre) => (
                <SelectItem key={genre} value={genre}>{genre}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Style */}
        <div className="w-[148px] shrink-0 h-full">
          <Select value={value.style || 'all'} onValueChange={(next) => update('style', next === 'all' ? undefined : (next as DigitalBookFilters['style']))}>
            <SelectTrigger className="h-full w-full rounded-none border-0 bg-transparent px-4 text-sm shadow-none ring-0 focus:ring-0 focus:ring-offset-0">
              <SelectValue placeholder="Style" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Styles</SelectItem>
              {styles.map((style) => (
                <SelectItem key={style} value={style} className="capitalize">{style}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}
