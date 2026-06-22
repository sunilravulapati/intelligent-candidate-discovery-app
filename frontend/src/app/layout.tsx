import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Redrob Intelligent Discovery",
  description: "Recruiter workspace for semantic candidate discovery and transparent ranking.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
