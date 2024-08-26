import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { FlowProvider } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AIOS",
  description: "Built & Hosted by AGI Research",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <script
        async
          type="module"
          defer
          src="https://cdn.jsdelivr.net/npm/ldrs/dist/auto/hatch.js"
        ></script>
      <body className={inter.className}>
        <FlowProvider>
          {children}
        </FlowProvider>
      </body>
    </html>
  );
}
