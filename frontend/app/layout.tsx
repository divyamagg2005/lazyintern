import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "LazyIntern Dashboard",
  description: "Analytics and controls for the LazyIntern internship outreach pipeline."
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-950 to-slate-900 text-slate-100">
        {children}
      </body>
    </html>
  );
}

