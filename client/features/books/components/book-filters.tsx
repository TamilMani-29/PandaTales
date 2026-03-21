'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { BookFilters, AgeGroup, Genre, BookType } from '@/types/book.types';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

type BookFiltersComponentProps = {
  filters: BookFilters;
  onFiltersChange: (filters: BookFilters) => void;
  showTypeFilter?: boolean;
};

const genres: Genre[] = ['Adventure', 'Fantasy', 'Superhero', 'Animals', 'Space', 'Detective', 'Educational', 'Nature'];
const ageGroups: AgeGroup[] = ['3-5', '6-8', '9-12'];
const bookTypes: BookType[] = ['single', 'series'];

export function BookFiltersComponent({ filters, onFiltersChange, showTypeFilter = true }: BookFiltersComponentProps) {
  const handleClearFilters = () => {
    onFiltersChange({});
  };

  const hasActiveFilters = Object.values(filters).some(v => v !== undefined);

  return (
    <Card className="sticky top-20 rounded-3xl shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Filters</CardTitle>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            className="h-8 px-2"
          >
            <X className="h-4 w-4 mr-1" />
            Clear
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <Label className="text-base font-semibold mb-3 block">Age Group</Label>
          <RadioGroup
            value={filters.ageGroup}
            onValueChange={(value) =>
              onFiltersChange({ ...filters, ageGroup: value as AgeGroup })
            }
          >
            {ageGroups.map((age) => (
              <div key={age} className="flex items-center space-x-2">
                <RadioGroupItem value={age} id={`age-${age}`} />
                <Label htmlFor={`age-${age}`} className="font-normal cursor-pointer">
                  {age} years
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        <div>
          <Label className="text-base font-semibold mb-3 block">Genre</Label>
          <div className="space-y-2">
            {genres.map((genre) => (
              <div key={genre} className="flex items-center space-x-2">
                <Checkbox
                  id={`genre-${genre}`}
                  checked={filters.genre === genre}
                  onCheckedChange={(checked) =>
                    onFiltersChange({
                      ...filters,
                      genre: checked ? genre : undefined,
                    })
                  }
                />
                <Label
                  htmlFor={`genre-${genre}`}
                  className="font-normal cursor-pointer"
                >
                  {genre}
                </Label>
              </div>
            ))}
          </div>
        </div>

        {showTypeFilter && (
          <div>
            <Label className="text-base font-semibold mb-3 block">Type</Label>
            <RadioGroup
              value={filters.type}
              onValueChange={(value) =>
                onFiltersChange({ ...filters, type: value as BookType })
              }
            >
              {bookTypes.map((type) => (
                <div key={type} className="flex items-center space-x-2">
                  <RadioGroupItem value={type} id={`type-${type}`} />
                  <Label
                    htmlFor={`type-${type}`}
                    className="font-normal cursor-pointer capitalize"
                  >
                    {type}
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        )}

        <div>
          <Label className="text-base font-semibold mb-3 block">
            Price Range: ₹{filters.minPrice || 0} - ₹{filters.maxPrice || 2000}
          </Label>
          <Slider
            min={0}
            max={2000}
            step={100}
            value={[filters.minPrice || 0, filters.maxPrice || 2000]}
            onValueChange={([min, max]) =>
              onFiltersChange({ ...filters, minPrice: min, maxPrice: max })
            }
            className="mt-2"
          />
        </div>
      </CardContent>
    </Card>
  );
}
