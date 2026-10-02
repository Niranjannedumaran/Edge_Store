import React from "react";

/**
 * EdgeStore Unified Brand Logo
 * Concept:
 * - Geometric isometric cube representing the physical Edge appliance node
 * - Right facet forms an architectural "E" for EdgeStore
 * - Left facet displays dual hardware storage drives (Primary + Replica)
 * - Central crown features the cryptographic Key-SD hardware shield
 * - Built purely with sharp, scalable SVGs & vibrant purple/violet/cyan gradients
 */
export function EdgeStoreLogo({ size = 32, showText = false, textClassName = "text-white font-bold text-base tracking-tight", subtitle = null }) {
  const gradientId = "es-logo-grad";
  const glowId = "es-logo-glow";
  const shieldGradId = "es-shield-grad";
  const driveGradId = "es-drive-grad";

  return (
    <div className="inline-flex items-center gap-3 select-none">
      <div
        style={{
          width: size,
          height: size,
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <svg
          viewBox="0 0 100 100"
          width={size}
          height={size}
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          style={{ overflow: "visible" }}
        >
          <defs>
            {/* Ambient Background Squircle Gradient */}
            <linearGradient id={`${gradientId}-bg`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1e1338" />
              <stop offset="50%" stopColor="#0d0818" />
              <stop offset="100%" stopColor="#040208" />
            </linearGradient>

            {/* Neon Border Gradient */}
            <linearGradient id={`${gradientId}-stroke`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#d8b4fe" stopOpacity="0.8" />
              <stop offset="45%" stopColor="#a855f7" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.3" />
            </linearGradient>

            {/* Facet E Gradient */}
            <linearGradient id={`${gradientId}-e`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f3e8ff" />
              <stop offset="35%" stopColor="#c084fc" />
              <stop offset="100%" stopColor="#7c3aed" />
            </linearGradient>

            {/* Dual Drives Left Gradient */}
            <linearGradient id={driveGradId} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#6366f1" />
              <stop offset="60%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#a855f7" />
            </linearGradient>

            {/* Shield Hardware Core Gradient */}
            <linearGradient id={shieldGradId} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="50%" stopColor="#818cf8" />
              <stop offset="100%" stopColor="#c084fc" />
            </linearGradient>

            {/* Subtle Neon Drop Shadow Filter */}
            <filter id={glowId} x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#a855f7" floodOpacity="0.35" />
            </filter>
          </defs>

          {/* Squircle Badge Plate */}
          <rect
            x="4"
            y="4"
            width="92"
            height="92"
            rx="24"
            fill={`url(#${gradientId}-bg)`}
            stroke={`url(#${gradientId}-stroke)`}
            strokeWidth="1.5"
            filter={`url(#${glowId})`}
          />

          {/* Subtly illuminated inner circuit grid lines */}
          <path
            d="M20 50L50 67L80 50M50 67V86"
            stroke="rgba(168, 85, 247, 0.15)"
            strokeWidth="1"
            strokeDasharray="2 2"
          />

          {/* =================================================================
              LEFT FACET: DUAL DRIVES (Primary + Replica mirrored storage tiers)
              ================================================================= */}
          {/* Drive 1 (Primary - Top) */}
          <g>
            <path
              d="M23 42L47 55V61L23 48Z"
              fill={`url(#${driveGradId})`}
              fillOpacity="0.85"
            />
            {/* Drive 1 Face Highlight */}
            <path
              d="M23 42L35 35L47 48L47 55L23 42Z"
              fill="#c084fc"
              fillOpacity="0.25"
            />
            {/* Drive 1 Status LED */}
            <circle cx="28" cy="46" r="1.5" fill="#34d399" />
          </g>

          {/* Drive 2 (Replica - Bottom) */}
          <g>
            <path
              d="M23 56L47 69V75L23 62Z"
              fill={`url(#${driveGradId})`}
              fillOpacity="0.85"
            />
            {/* Drive 2 Face Highlight */}
            <path
              d="M23 56L35 49L47 62L47 69L23 56Z"
              fill="#c084fc"
              fillOpacity="0.25"
            />
            {/* Drive 2 Status LED */}
            <circle cx="28" cy="60" r="1.5" fill="#38bdf8" />
          </g>

          {/* =================================================================
              RIGHT FACET: ARCHITECTURAL "E" INTERLOCK
              ================================================================= */}
          {/* Vertical spine & 3 horizontal arms forming an isometric E */}
          <path
            d="
              M53 32 L77 18 L77 26 L61 35 L61 44 L75 36 L75 44 L61 52 L61 63 L77 54 L77 62 L53 76 Z
            "
            fill={`url(#${gradientId}-e)`}
            stroke="rgba(255, 255, 255, 0.4)"
            strokeWidth="0.75"
          />

          {/* =================================================================
              CENTER TOP: HARDWARE KEY-SD SHIELD (Cryptographic Interlock)
              ================================================================= */}
          <g transform="translate(40, 15)">
            {/* Shield Outline */}
            <path
              d="M10 2L18 6V13C18 18 10 23 10 23C10 23 2 18 2 13V6L10 2Z"
              fill={`url(#${shieldGradId})`}
              stroke="#ffffff"
              strokeWidth="1"
            />
            {/* Keyhole / Lock Core in Shield */}
            <circle cx="10" cy="10" r="2.2" fill="#09090d" />
            <path d="M9 10H11L11.5 15H8.5L9 10Z" fill="#09090d" />
          </g>
        </svg>
      </div>

      {showText && (
        <div className="flex flex-col text-left">
          <div className="flex items-center gap-1.5">
            <span className={textClassName}>EdgeStore</span>
            <span className="text-[9px] px-1.5 py-0.2 rounded font-mono font-bold bg-purple-500/15 border border-purple-500/30 text-purple-300">
              LUKS2
            </span>
          </div>
          {subtitle && (
            <span className="text-[10px] text-slate-400 font-mono tracking-wider uppercase">
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default EdgeStoreLogo;
