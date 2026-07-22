import type { Metadata } from "next";
// Added by Jullianna: imported Fraunces because page.tsx styles reference
// "Fraunces" but the font was never loaded, so it silently fell back to
// the browser's default serif.
import { Geist, Geist_Mono, Fraunces } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
    variable: "--font-geist-sans",
    subsets: ["latin"],
});

const geistMono = Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"],
});

// Added by Jullianna: loads Fraunces and exposes it as the CSS variable
// --font-fraunces so any component can use it for headings
const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
});

// Added by Jullianna: replaced the default create-next-app metadata with
// the real project name so the browser tab reads "Sprout".
export const metadata: Metadata = {
  title: "Sprout",
  description: "Plant care tracker",
};

export default function RootLayout({
                                       children,
                                   }: Readonly<{
    children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      // Added by Jullianna: added ${fraunces.variable} so --font-fraunces
      // is available everywhere inside the app
      className={`${geistSans.variable} ${geistMono.variable} ${fraunces.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}