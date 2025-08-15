import React from 'react';
import { ThemeProvider } from './context/ThemeContext';

export const withTheme = (ui: React.ReactElement) => (
  <ThemeProvider>{ui}</ThemeProvider>
);

