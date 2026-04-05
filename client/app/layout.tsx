import './globals.css';
import type { Metadata } from 'next';
import { Quicksand, Inter } from 'next/font/google';
import { ReactQueryProvider } from '@/lib/providers/react-query-provider';
// AUTH: import { AuthProvider } from '@/lib/providers/auth-provider';
import { Toaster } from '@/components/ui/sonner';
import { Header } from '@/components/layout/header';
import { FloatingClouds } from '@/components/shared/floating-clouds';

const quicksand = Quicksand({
  subsets: ['latin'],
  variable: '--font-quicksand',
});

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Pandora Pages - Crafted For You',
  description: 'Create magical personalized coloring books for your child, crafted just for them',
  icons: {
    icon: '/logo_without_name.jpeg',
    apple: '/logo_without_name.jpeg',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${quicksand.variable} ${inter.variable} font-sans`}>
        <ReactQueryProvider>
          {/* AUTH: <AuthProvider> — re-enable when authentication is introduced */}
            <FloatingClouds />
            <Header />
            {children}
            <Toaster />
          {/* AUTH: </AuthProvider> */}
        </ReactQueryProvider>
      </body>
    </html>
  );
}
