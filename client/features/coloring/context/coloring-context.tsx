'use client';

import React, { createContext, useContext, useReducer } from 'react';
import { PublicTheme } from '@/types/book.types';

// ── State ─────────────────────────────────────────────────────────────────────

interface ColoringFormData {
  childName: string;
  childAge: number;
  parentEmail: string;
}

interface ColoringCreationState {
  mode: 'photo' | 'theme' | null;
  selectedTheme: PublicTheme | null;
  pageCount: number;
  formData: ColoringFormData;
}

// ── Actions ───────────────────────────────────────────────────────────────────

type ColoringAction =
  | { type: 'SET_MODE'; payload: 'photo' | 'theme' | null }
  | { type: 'SET_THEME'; payload: PublicTheme }
  | { type: 'SET_PAGE_COUNT'; payload: number }
  | { type: 'SET_FORM_DATA'; payload: Partial<ColoringFormData> }
  | { type: 'RESET' };

// ── Initial state ─────────────────────────────────────────────────────────────

const initialState: ColoringCreationState = {
  mode: null,
  selectedTheme: null,
  pageCount: 16,
  formData: {
    childName: '',
    childAge: 5,
    parentEmail: '',
  },
};

// ── Reducer ───────────────────────────────────────────────────────────────────

function coloringReducer(
  state: ColoringCreationState,
  action: ColoringAction
): ColoringCreationState {
  switch (action.type) {
    case 'SET_MODE':
      // Reset theme-specific state when switching modes
      return { ...initialState, mode: action.payload };
    case 'SET_THEME':
      return { ...state, selectedTheme: action.payload };
    case 'SET_PAGE_COUNT':
      return { ...state, pageCount: action.payload };
    case 'SET_FORM_DATA':
      return { ...state, formData: { ...state.formData, ...action.payload } };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

// ── Context ───────────────────────────────────────────────────────────────────

interface ColoringContextValue {
  state: ColoringCreationState;
  dispatch: React.Dispatch<ColoringAction>;
}

const ColoringContext = createContext<ColoringContextValue | undefined>(undefined);

export function ColoringProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(coloringReducer, initialState);
  return (
    <ColoringContext.Provider value={{ state, dispatch }}>
      {children}
    </ColoringContext.Provider>
  );
}

export function useColoringContext() {
  const ctx = useContext(ColoringContext);
  if (!ctx) {
    throw new Error('useColoringContext must be used within a ColoringProvider');
  }
  return ctx;
}
