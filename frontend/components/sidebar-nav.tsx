"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface Section {
  href: string;
  label: string;
  detail: string;
  icon: "overview" | "camera" | "map" | "weather" | "review";
}

const SECTIONS: Section[] = [
  {
    href: "/",
    label: "Overview",
    detail: "Platform state and scope",
    icon: "overview",
  },
  {
    href: "/chat",
    label: "Photo assessment",
    detail: "Assistive image triage",
    icon: "camera",
  },
  {
    href: "/outlook",
    label: "Area outlook",
    detail: "Separate forecast output",
    icon: "map",
  },
  {
    href: "/weather",
    label: "Weather",
    detail: "Conditions and 7-day forecast",
    icon: "weather",
  },
  {
    href: "/review",
    label: "Review queue",
    detail: "Expert verification",
    icon: "review",
  },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

function Icon({ name }: { name: Section["icon"] }) {
  const common = {
    width: 18,
    height: 18,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
    focusable: false,
  };

  switch (name) {
    case "overview":
      return (
        <svg {...common}>
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
        </svg>
      );
    case "camera":
      return (
        <svg {...common}>
          <path d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z" />
          <circle cx="12" cy="13" r="3.2" />
        </svg>
      );
    case "map":
      return (
        <svg {...common}>
          <path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2Z" />
          <path d="M9 4v14" />
          <path d="M15 6v14" />
        </svg>
      );
    case "weather":
      return (
        <svg {...common}>
          <circle cx="8" cy="9" r="2.6" />
          <path d="M8 3.6v1M8 13.4v1M3.6 9h1M11.4 9h-1" />
          <path d="M17.5 19a3 3 0 0 0-.5-5.96A4.2 4.2 0 0 0 9.2 14a3 3 0 0 0 .3 5Z" />
        </svg>
      );
    case "review":
      return (
        <svg {...common}>
          <path d="M9 4h6l1 2h3a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h3l1-2Z" />
          <path d="m8.5 13 2.2 2.2L16 10" />
        </svg>
      );
  }
}

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <nav className="app-nav" aria-label="Sections">
      <p className="app-nav-heading">Workspace</p>
      <ul className="app-nav-list">
        {SECTIONS.map((section) => {
          const active = isActive(pathname, section.href);
          return (
            <li key={section.href}>
              <Link
                href={section.href}
                className={active ? "app-nav-link app-nav-link-active" : "app-nav-link"}
                aria-current={active ? "page" : undefined}
              >
                <span className="app-nav-icon">
                  <Icon name={section.icon} />
                </span>
                <span className="app-nav-text">
                  <span className="app-nav-label">{section.label}</span>
                  <span className="app-nav-detail">{section.detail}</span>
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
