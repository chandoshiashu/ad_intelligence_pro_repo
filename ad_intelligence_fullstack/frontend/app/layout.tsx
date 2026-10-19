import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ad Intelligence",
  description: "Evidence-backed competitor advertising intelligence",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
