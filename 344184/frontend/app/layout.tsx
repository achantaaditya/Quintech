import "./styles.css";
import type { Metadata } from "next";
export const metadata: Metadata = { title: "CareerOS — Your AI Career Engineer", description: "Understand. Prepare. Match. Get Career-Ready." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
