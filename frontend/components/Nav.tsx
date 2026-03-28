"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function Nav() {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const links = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/upload", label: "Upload" },
  ];

  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/dashboard" className="text-lg font-bold text-gray-900">
          PodcastAI
        </Link>

        <div className="flex items-center gap-6">
          {user && links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm transition-colors ${
                pathname.startsWith(link.href)
                  ? "font-medium text-blue-600"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              {link.label}
            </Link>
          ))}

          {user ? (
            <div className="flex items-center gap-4">
              <Link
                href="/settings"
                className="text-sm text-gray-500 hover:text-gray-900"
              >
                Settings
              </Link>
              <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 capitalize">
                {user.plan}
              </span>
              <button
                onClick={logout}
                className="text-sm text-gray-400 hover:text-gray-700"
              >
                Sign out
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link href="/" className="text-sm text-gray-500 hover:text-gray-900">
                Sign in
              </Link>
              <Link
                href="/onboarding"
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
              >
                Get started
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
