import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Redrob Discovery",
  description: "AI-Powered Candidate Intelligence for recruiters.",
};

import { ToastContainer } from "@/components/Toast";

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
        <ToastContainer />
      </body>
    </html>
  );
}
