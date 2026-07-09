import { render, screen } from '@testing-library/react';
import App from './App';

beforeEach(() => {
  // App fetches status and saved configs on mount; return a non-success
  // payload so no state updates fire outside the test's render
  global.fetch = jest.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'error' }) })
  );
});

test('renders the control panel', () => {
  render(<App />);
  expect(screen.getByText(/LED Flux Control/i)).toBeInTheDocument();
  expect(screen.getByText(/Turn On/i)).toBeInTheDocument();
  expect(screen.getByText(/Build Custom Scene/i)).toBeInTheDocument();
});
