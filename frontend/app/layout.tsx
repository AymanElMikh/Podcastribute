import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import Nav from "@/components/Nav";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PodcastAI — Turn episodes into content",
  description: "AI-powered podcast repurposing engine",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${geist.className} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-gray-50 text-gray-900">
        <Nav />
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
