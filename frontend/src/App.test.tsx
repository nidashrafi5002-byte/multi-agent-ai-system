import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the MAIA product experience', () => {
  render(<App />);

  expect(screen.getAllByText(/MAIA/i).length).toBeGreaterThan(0);
  expect(screen.getByRole('heading', { name: /Welcome to MAIA/i })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: /Launch an agent/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Analyze AAPL Q3 earnings/i })).toBeInTheDocument();
});
