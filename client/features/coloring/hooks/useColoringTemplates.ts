import { useQuery } from '@tanstack/react-query';
import { coloringTemplatesService } from '../services/coloring-templates.service';
import { ColoringTemplateFilters } from '@/types/book.types';

export const COLORING_QUERY_KEYS = {
  templates: (filters: ColoringTemplateFilters) =>
    ['coloringTemplates', filters] as const,
  template: (id: string) => ['coloringTemplate', id] as const,
  themesList: () => ['coloringThemesList'] as const,
  activeThemes: () => ['activeThemes'] as const,
};

/**
 * Paginated list of coloring book templates from GET /api/v1/coloring-books.
 * Supports server-side filtering, sorting and pagination.
 */
export function useColoringTemplates(filters: ColoringTemplateFilters = {}) {
  return useQuery({
    queryKey: COLORING_QUERY_KEYS.templates(filters),
    queryFn: () => coloringTemplatesService.getTemplates(filters),
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * Single coloring book template details from GET /api/v1/coloring-books/{id}.
 */
export function useColoringTemplate(id: string) {
  return useQuery({
    queryKey: COLORING_QUERY_KEYS.template(id),
    queryFn: () => coloringTemplatesService.getTemplateById(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * Distinct theme strings used by existing templates (for filter dropdowns).
 * From GET /api/v1/coloring-books/themes/list.
 */
export function useColoringThemesList() {
  return useQuery({
    queryKey: COLORING_QUERY_KEYS.themesList(),
    queryFn: coloringTemplatesService.getThemesList,
    staleTime: 1000 * 60 * 15,
  });
}

/**
 * Active generation themes for the theme-based creation flow.
 * From GET /api/v1/themes.
 */
export function useActiveThemes() {
  return useQuery({
    queryKey: COLORING_QUERY_KEYS.activeThemes(),
    queryFn: coloringTemplatesService.getActiveThemes,
    staleTime: 1000 * 60 * 15,
  });
}
