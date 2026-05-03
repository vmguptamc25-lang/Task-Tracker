import './globals.css';
import { Toaster } from 'sonner';

export const metadata = {
  title: 'TaskFlow — Organize Your Day',
  description: 'A beautiful, fast task tracker with real authentication.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="antialiased bg-background text-foreground">
        {children}
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
