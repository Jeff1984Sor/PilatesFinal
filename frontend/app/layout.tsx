import "./globals.css";
import { Space_Grotesk, Fraunces } from "next/font/google";
import Providers from "./providers";

const space = Space_Grotesk({ subsets: ["latin"], variable: "--font-sans" });
const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-display" });

export const metadata = {
  title: "StudioPilates",
  description: "Modern Pilates Studio management"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${space.variable} ${fraunces.variable}`}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
