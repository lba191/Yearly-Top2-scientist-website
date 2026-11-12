import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Scientist Trends | Annual Citation Impact Explorer",
  description:
    "Explore rank, institution, country, and field trends across annual science-wide citation indicator releases.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
