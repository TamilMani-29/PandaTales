'use client';

import { Slider } from '@/components/ui/slider';
import { BookFilters, AgeGroup, Genre, BookType } from '@/types/book.types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SlidersHorizontal, X, BookOpen, Layers } from 'lucide-react';
import { cn } from '@/lib/utils';

type BookFiltersComponentProps = {
  filters: BookFilters;
  onFiltersChange: (filters: BookFilters) => void;
  showTypeFilter?: boolean;
  className?: string;
};

const genreConfig: { value: Genre; emoji: string }[] = [
  { value: 'Adventure', emoji: '🗺️' },
  { value: 'Fantasy', emoji: '🧙' },
  { value: 'Superhero', emoji: '🦸' },
  { value: 'Animals', emoji: '🐾' },
  { value: 'Space', emoji: '🚀' },
  { value: 'Detective', emoji: '🔍' },
  { value: 'Educational', emoji: '📚' },
  { value: 'Nature', emoji: '🌿' },
];

const ageGroups: { value: AgeGroup; label: string }[] = [
  { value: '3-5', label: '3–5 yrs' },
  { value: '6-8', label: '6–8 yrs' },
  { value: '9-12', label: '9–12 yrs' },
];

const bookTypes: { value: BookType; label: string; description: string }[] = [
  { value: 'single', label: 'Single Book', description: 'One complete story' },
  { value: 'series', label: 'Series', description: 'Multi-part adventure' },
];

export function BookFiltersComponent({ filters, onFiltersChange, showTypeFilter = true, className }: BookFiltersComponentProps) {
  const handleClearFilters = () => {
    onFiltersChange({});
  };

  const toggle = <T,>(current: T[] | undefined, value: T): T[] | undefined => {
    if (!current || current.length === 0) return [value];
    const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value];
    return next.length === 0 ? undefined : next;
  };

  const activeFilterCount = [
    filters.ageGroup?.length ? 'age' : undefined,
    filters.genre?.length ? 'genre' : undefined,
    filters.type?.length ? 'type' : undefined,
    filters.minPrice !== undefined || filters.maxPrice !== undefined ? 'price' : undefined,
  ].filter(Boolean).length;

  const minPrice = filters.minPrice ?? 0;
  const maxPrice = filters.maxPrice ?? 2000;

  return (
    <div className={cn('sticky top-20 space-y-1', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-1 mb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-gradient-to-br from-pink-100 to-purple-100 dark:from-pink-900/30 dark:to-purple-900/30">
            <SlidersHorizontal className="h-4 w-4 text-pink-600 dark:text-pink-400" />
          </div>
          <span className="font-semibold text-base">Filters</span>
          {activeFilterCount > 0 && (
            <Badge className="h-5 min-w-5 px-1.5 text-xs bg-gradient-to-r from-pink-500 to-purple-500 text-white border-0">
              {activeFilterCount}
            </Badge>
          )}
        </div>
        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground gap-1"
          >
            <X className="h-3 w-3" />
            Clear all
          </Button>
        )}
      </div>

      {/* Age Group */}
      <div className="rounded-2xl border bg-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-foreground/80 uppercase tracking-wide">Age Group</p>
          {filters.ageGroup?.length ? (
            <span className="text-xs text-muted-foreground">{filters.ageGroup.length} selected</span>
          ) : (
            <span className="text-xs text-muted-foreground">Select all that apply</span>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {ageGroups.map(({ value, label }) => {
            const isActive = filters.ageGroup?.includes(value) ?? false;
            return (
              <button
                key={value}
                onClick={() =>
                  onFiltersChange({
                    ...filters,
                    ageGroup: toggle(filters.ageGroup, value),
                  })
                }
                className={cn(
                  'px-3 py-1.5 rounded-xl text-sm font-medium transition-all duration-150 border',
                  isActive
                    ? 'bg-gradient-to-r from-pink-500 to-purple-500 text-white border-transparent shadow-sm'
                    : 'bg-muted/50 text-muted-foreground border-transparent hover:border-pink-200 hover:text-foreground hover:bg-muted'
                )}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Genre */}
      <div className="rounded-2xl border bg-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-foreground/80 uppercase tracking-wide">Genre</p>
          {filters.genre?.length ? (
            <span className="text-xs text-muted-foreground">{filters.genre.length} selected</span>
          ) : (
            <span className="text-xs text-muted-foreground">Select all that apply</span>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {genreConfig.map(({ value, emoji }) => {
            const isActive = filters.genre?.includes(value) ?? false;
            return (
              <button
                key={value}
                onClick={() =>
                  onFiltersChange({
                    ...filters,
                    genre: toggle(filters.genre, value),
                  })
                }
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-medium transition-all duration-150 border',
                  isActive
                    ? 'bg-gradient-to-r from-pink-500 to-purple-500 text-white border-transparent shadow-sm'
                    : 'bg-muted/50 text-muted-foreground border-transparent hover:border-pink-200 hover:text-foreground hover:bg-muted'
                )}
              >
                <span className="text-base leading-none">{emoji}</span>
                {value}
              </button>
            );
          })}
        </div>
      </div>

      {/* Book Type */}
      {showTypeFilter && (
        <div className="rounded-2xl border bg-card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-foreground/80 uppercase tracking-wide">Book Type</p>
            {filters.type?.length ? (
              <span className="text-xs text-muted-foreground">{filters.type.length} selected</span>
            ) : (
              <span className="text-xs text-muted-foreground">Select all that apply</span>
            )}
          </div>
          <div className="space-y-2">
            {bookTypes.map(({ value, label, description }) => {
              const isActive = filters.type?.includes(value) ?? false;
              return (
                <button
                  key={value}
                  onClick={() =>
                    onFiltersChange({
                      ...filters,
                      type: toggle(filters.type, value),
                    })
                  }
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-150 border',
                    isActive
                      ? 'bg-gradient-to-r from-pink-50 to-purple-50 dark:from-pink-900/20 dark:to-purple-900/20 border-pink-300 dark:border-pink-700'
                      : 'border-transparent hover:border-muted-foreground/20 hover:bg-muted/50'
                  )}
                >
                  <div className={cn(
                    'p-1.5 rounded-lg transition-colors',
                    isActive
                      ? 'bg-gradient-to-br from-pink-500 to-purple-500 text-white'
                      : 'bg-muted text-muted-foreground'
                  )}>
                    {value === 'single' ? <BookOpen className="h-3.5 w-3.5" /> : <Layers className="h-3.5 w-3.5" />}
                  </div>
                  <div>
                    <p className={cn('text-sm font-medium', isActive ? 'text-foreground' : 'text-muted-foreground')}>{label}</p>
                    <p className="text-xs text-muted-foreground">{description}</p>
                  </div>
                  {isActive && (
                    <div className="ml-auto w-2 h-2 rounded-full bg-gradient-to-r from-pink-500 to-purple-500" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Price Range */}
      <div className="rounded-2xl border bg-card p-4 space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-foreground/80 uppercase tracking-wide">Price Range</p>
          <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
            ₹{minPrice} – ₹{maxPrice}
          </span>
        </div>
        <Slider
          min={0}
          max={2000}
          step={100}
          value={[minPrice, maxPrice]}
          onValueChange={([min, max]) =>
            onFiltersChange({ ...filters, minPrice: min, maxPrice: max })
          }
          className="mt-1"
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>₹0</span>
          <span>₹2,000</span>
        </div>
      </div>
    </div>
  );
}
