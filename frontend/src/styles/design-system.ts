/**
 * Design System - Reusable styles following UX best practices
 * 
 * This file contains all reusable style objects that ensure consistency
 * across the application and follow modern UI/UX principles.
 */

import { CSSProperties } from 'react';

// ============================================================================
// COLORS
// ============================================================================

export const colors = {
  primary: {
    main: '#2563eb',
    hover: '#1d4ed8',
    light: '#dbeafe',
    dark: '#1e40af',
  },
  secondary: {
    main: '#64748b',
    hover: '#475569',
    light: '#f1f5f9',
    dark: '#334155',
  },
  success: {
    main: '#10b981',
    hover: '#059669',
    light: '#d1fae5',
    dark: '#047857',
  },
  warning: {
    main: '#f59e0b',
    hover: '#d97706',
    light: '#fef3c7',
    dark: '#b45309',
  },
  error: {
    main: '#ef4444',
    hover: '#dc2626',
    light: '#fee2e2',
    dark: '#b91c1c',
  },
  info: {
    main: '#3b82f6',
    hover: '#2563eb',
    light: '#dbeafe',
    dark: '#1d4ed8',
  },
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
};

// ============================================================================
// SPACING
// ============================================================================

export const spacing = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '3rem',
  '3xl': '4rem',
};

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  fontFamily: {
    sans: `-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif`,
    mono: `'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace`,
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
};

// ============================================================================
// SHADOWS
// ============================================================================

export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
};

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const borderRadius = {
  sm: '0.375rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1rem',
  full: '9999px',
};

// ============================================================================
// TRANSITIONS
// ============================================================================

export const transitions = {
  fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  base: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
};

// ============================================================================
// COMPONENT STYLES
// ============================================================================

export const components = {
  // Buttons
  button: {
    base: {
      padding: `${spacing.sm} ${spacing.lg}`,
      borderRadius: borderRadius.md,
      fontSize: typography.fontSize.base,
      fontWeight: typography.fontWeight.medium,
      border: 'none',
      cursor: 'pointer',
      transition: `all ${transitions.base}`,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: spacing.sm,
      lineHeight: typography.lineHeight.normal,
    } as CSSProperties,
    primary: {
      backgroundColor: colors.primary.main,
      color: 'white',
    } as CSSProperties,
    secondary: {
      backgroundColor: colors.secondary.main,
      color: 'white',
    } as CSSProperties,
    success: {
      backgroundColor: colors.success.main,
      color: 'white',
    } as CSSProperties,
    warning: {
      backgroundColor: colors.warning.main,
      color: 'white',
    } as CSSProperties,
    error: {
      backgroundColor: colors.error.main,
      color: 'white',
    } as CSSProperties,
    outline: {
      backgroundColor: 'transparent',
      border: `2px solid ${colors.primary.main}`,
      color: colors.primary.main,
    } as CSSProperties,
    ghost: {
      backgroundColor: 'transparent',
      color: colors.gray[700],
    } as CSSProperties,
  },

  // Cards
  card: {
    base: {
      backgroundColor: 'white',
      borderRadius: borderRadius.lg,
      boxShadow: shadows.md,
      padding: spacing.xl,
      transition: `all ${transitions.base}`,
    } as CSSProperties,
    hover: {
      boxShadow: shadows.lg,
      transform: 'translateY(-2px)',
    } as CSSProperties,
  },

  // Inputs
  input: {
    base: {
      padding: `${spacing.sm} ${spacing.md}`,
      border: `1px solid ${colors.gray[300]}`,
      borderRadius: borderRadius.md,
      fontSize: typography.fontSize.base,
      lineHeight: typography.lineHeight.normal,
      transition: `all ${transitions.base}`,
      width: '100%',
    } as CSSProperties,
    focus: {
      borderColor: colors.primary.main,
      boxShadow: `0 0 0 3px ${colors.primary.light}`,
      outline: 'none',
    } as CSSProperties,
  },

  // Badges
  badge: {
    base: {
      display: 'inline-flex',
      alignItems: 'center',
      padding: `${spacing.xs} ${spacing.sm}`,
      borderRadius: borderRadius.full,
      fontSize: typography.fontSize.xs,
      fontWeight: typography.fontWeight.medium,
      textTransform: 'capitalize' as const,
    } as CSSProperties,
    success: {
      backgroundColor: colors.success.light,
      color: colors.success.dark,
    } as CSSProperties,
    warning: {
      backgroundColor: colors.warning.light,
      color: colors.warning.dark,
    } as CSSProperties,
    error: {
      backgroundColor: colors.error.light,
      color: colors.error.dark,
    } as CSSProperties,
    info: {
      backgroundColor: colors.info.light,
      color: colors.info.dark,
    } as CSSProperties,
    neutral: {
      backgroundColor: colors.gray[100],
      color: colors.gray[700],
    } as CSSProperties,
  },

  // Alerts
  alert: {
    base: {
      padding: spacing.md,
      borderRadius: borderRadius.md,
      fontSize: typography.fontSize.sm,
      lineHeight: typography.lineHeight.relaxed,
      display: 'flex',
      alignItems: 'flex-start',
      gap: spacing.sm,
    } as CSSProperties,
    success: {
      backgroundColor: colors.success.light,
      color: colors.success.dark,
      border: `1px solid ${colors.success.main}`,
    } as CSSProperties,
    warning: {
      backgroundColor: colors.warning.light,
      color: colors.warning.dark,
      border: `1px solid ${colors.warning.main}`,
    } as CSSProperties,
    error: {
      backgroundColor: colors.error.light,
      color: colors.error.dark,
      border: `1px solid ${colors.error.main}`,
    } as CSSProperties,
    info: {
      backgroundColor: colors.info.light,
      color: colors.info.dark,
      border: `1px solid ${colors.info.main}`,
    } as CSSProperties,
  },
};

// ============================================================================
// LAYOUT UTILITIES
// ============================================================================

export const layout = {
  container: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: `0 ${spacing.xl}`,
  } as CSSProperties,
  
  flexCenter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  } as CSSProperties,
  
  flexBetween: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  } as CSSProperties,
  
  grid: {
    display: 'grid',
    gap: spacing.lg,
  } as CSSProperties,
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Merge multiple style objects
 */
export const mergeStyles = (...styles: (CSSProperties | undefined)[]): CSSProperties => {
  return Object.assign({}, ...styles.filter(Boolean));
};

/**
 * Get responsive grid columns
 */
export const getGridColumns = (minWidth: string = '300px'): CSSProperties => ({
  gridTemplateColumns: `repeat(auto-fit, minmax(${minWidth}, 1fr))`,
});

/**
 * Truncate text with ellipsis
 */
export const truncateText = (lines: number = 1): CSSProperties => ({
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  display: '-webkit-box',
  WebkitLineClamp: lines,
  WebkitBoxOrient: 'vertical',
});
