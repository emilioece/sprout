import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
    variable: "--font-geist-sans",
    subsets: ["latin"],
});

const geistMono = Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"],
});

export const metadata: Metadata = {
    title: "Sprout",
    description: "Plant care made simple",
};

export default function RootLayout({
                                       children,
                                   }: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html
            lang="en"
            className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
        >
        <body className="min-h-full flex">
        {/* sidebar */}
        <aside
            className="w-64 bg-white border-r px-4 py-6 flex flex-col"
            style={{ borderColor: "var(--border)" }}
        >
            {/* logo + plant count in top left */}
            <div className="mb-8">
                <div className="flex items-center gap-2 mb-1">
                    <span className="text-2xl">🌱</span>
                    <span
                        className="text-xl font-semibold"
                        style={{ fontFamily: "'Fraunces', serif", color: "var(--foreground)" }}
                    >
                        Sprout
                    </span>
                </div>
                <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>
                    0 plants in collection
                </p>
            </div>

            {/* different pages buttons */}
            <nav className="flex flex-col gap-1">
                <a
                    href="#"
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium"
                    style={{ background: "#3A4A32", color: "#FFFFFF" }}
                >
                    <span>🏠</span>
                    Dashboard
                </a>

                <a
                    href="#"
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium hover:bg-gray-50"
                    style={{ color: "var(--foreground)" }}
                >
                    <span>🌿</span>
                    My Plants
                </a>

                <a
                    href="#"
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium hover:bg-gray-50"
                    style={{ color: "var(--foreground)" }}
                >
                    <span>📅</span>
                    Schedule
                </a>

                <a
                    href="#"
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium hover:bg-gray-50"
                    style={{ color: "var(--foreground)" }}
                >
                    <span>🔍</span>
                    Symptom Guide
                </a>
            </nav>

            {/* spacer for empty space */}
            <div className="flex-1" />

            {/* tip box */}
            <div
                className="rounded-xl p-4 mb-4 text-sm"
                style={{ background: "#EEF1EA" }}
            >
                <p className="font-medium mb-1" style={{ color: "var(--foreground)" }}>
                    💡 Tip for beginners
                </p>
                <p style={{ color: "var(--muted-foreground)" }}>
                    Check the Dashboard daily — it shows exactly what needs attention today.
                </p>
            </div>

            {/* add plant button */}
            <button
                className="px-6 py-3 rounded-xl text-sm font-medium transition-all hover:opacity-90"
                style={{ background: "#3A4A32", color: "#FFFFFF" }}
            >
                + Add Plant
            </button>
        </aside>

        <div className="flex-1 flex flex-col">{children}</div>
        </body>
        </html>
    );
}