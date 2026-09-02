import React, { useState, useEffect, useRef } from "react";
import {
  Layers,
  Search,
  Terminal,
  Lock,
  Activity,
  Server,
  Database,
  Shield,
  ArrowUpRight,
  ArrowDownRight,
  Code2,
  Check,
  ArrowRight,
  Globe,
  ShieldCheck,
  BarChart2,
  Zap,
  GitBranch,
  BoxSelect,
  Cpu,
  Globe2,
  Sparkles,
  CreditCard,
  History,
  FolderLock,
  HardDrive,
  RefreshCw,
  X
} from "lucide-react";

export function HeroLanding({ onGetStarted, user }) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const [activeTab, setActiveTab] = useState("cli");
  const [showCredsModal, setShowCredsModal] = useState(false);

  // Mouse spotlight tracker updating --mouse-x and --mouse-y CSS variables
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        containerRef.current.style.setProperty("--mouse-x", `${x}px`);
        containerRef.current.style.setProperty("--mouse-y", `${y}px`);
      }
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // 3D Canvas Particle Network with Line Connections (Tidiane Tambadou / Adrino Labs hybrid)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let animationFrameId;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const particleCount = 75;
    const particles = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.45,
        vy: (Math.random() - 0.5) * 0.45,
        radius: Math.random() * 1.5 + 0.5,
        alpha: Math.random() * 0.5 + 0.2,
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw lines between proximate particles
      for (let i = 0; i < particleCount; i++) {
        for (let j = i + 1; j < particleCount; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 110) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(168, 85, 247, ${0.12 * (1 - dist / 110)})`;
            ctx.lineWidth = 0.75;
            ctx.stroke();
          }
        }
      }

      // Draw & update particles
      particles.forEach((p) => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(192, 132, 252, ${p.alpha})`;
        ctx.fill();

        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative min-h-screen w-full bg-[#020204] text-slate-400 font-sans antialiased overflow-x-hidden selection:bg-purple-500/30"
      style={{
        backgroundColor: "#020204",
        color: "#94a3b8",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "--mouse-x": "50vw",
        "--mouse-y": "320px",
      }}
    >
      {/* =========================================================================
          CUSTOM EMBEDDED STYLES & ANIMATIONS
          ========================================================================= */}
      <style>{`
        /* Mouse Spotlight Glow */
        .spotlight-overlay {
          position: absolute;
          inset: 0;
          pointer-events: none;
          background: radial-gradient(900px circle at var(--mouse-x) var(--mouse-y), rgba(168, 85, 247, 0.09), transparent 45%);
          z-index: 1;
        }

        /* Tech Grid */
        .tech-grid {
          position: absolute;
          inset: 0;
          background-image: 
            linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
          background-size: 60px 60px;
          pointer-events: none;
          z-index: 2;
        }

        /* 5 Sparse Falling Lines */
        @keyframes fallingLine {
          0% { transform: translateY(-300px); opacity: 0; }
          20% { opacity: 0.7; }
          80% { opacity: 0.7; }
          100% { transform: translateY(130vh); opacity: 0; }
        }
        .falling-line {
          position: absolute;
          width: 1px;
          height: 140px;
          background: linear-gradient(to bottom, transparent, rgba(168, 85, 247, 0.8), transparent);
          pointer-events: none;
          z-index: 2;
        }
        .line-1 { left: 14%; animation: fallingLine 7s cubic-bezier(0.4, 0, 0.2, 1) infinite; animation-delay: 0s; }
        .line-2 { left: 33%; animation: fallingLine 9s cubic-bezier(0.4, 0, 0.2, 1) infinite; animation-delay: 1.5s; }
        .line-3 { left: 54%; animation: fallingLine 6.5s cubic-bezier(0.4, 0, 0.2, 1) infinite; animation-delay: 3s; }
        .line-4 { left: 76%; animation: fallingLine 8s cubic-bezier(0.4, 0, 0.2, 1) infinite; animation-delay: 0.8s; }
        .line-5 { left: 91%; animation: fallingLine 10s cubic-bezier(0.4, 0, 0.2, 1) infinite; animation-delay: 2.2s; }

        /* Conic Gradient Glow Button Border */
        @keyframes rotateConic {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .btn-glow-border {
          position: relative;
          border-radius: 9999px;
          padding: 1px;
          overflow: hidden;
          display: inline-flex;
        }
        .btn-glow-border::before {
          content: '';
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: conic-gradient(transparent, rgba(168, 85, 247, 0.95), transparent 35%);
          animation: rotateConic 4s linear infinite;
        }

        /* 3D Dashboard Perspective & Smooth Transition */
        .dashboard-container {
          perspective: 1200px;
          transform-style: preserve-3d;
        }
        .dashboard-card {
          transform: rotateX(20deg);
          transition: transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.6s ease;
          box-shadow: 0 30px 100px -20px rgba(0, 0, 0, 0.9), 0 0 60px rgba(168, 85, 247, 0.15);
        }
        .dashboard-card:hover {
          transform: rotateX(5deg);
          box-shadow: 0 35px 120px -20px rgba(0, 0, 0, 0.95), 0 0 80px rgba(168, 85, 247, 0.25);
        }

        /* Scanline Overlay Animation */
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(1200%); }
        }
        .scanline-bar {
          position: absolute;
          inset: 0;
          height: 80px;
          background: linear-gradient(to bottom, transparent, rgba(168, 85, 247, 0.09), transparent);
          pointer-events: none;
          animation: scanline 8s linear infinite;
          z-index: 30;
        }

        /* Horizon Ring */
        .horizon-ring {
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%) translateY(40%);
          width: 150vw;
          height: 50vw;
          border-radius: 50%;
          border-top: 1px solid rgba(168, 85, 247, 0.25);
          background: radial-gradient(ellipse at 50% 0%, rgba(168, 85, 247, 0.1), transparent 70%);
          pointer-events: none;
          z-index: 5;
        }

        /* Wireframe Torus Knot Spin Animation */
        @keyframes knotSpin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .knot-container {
          animation: knotSpin 50s linear infinite;
        }

        /* Flow Beam Animation for Onboarding */
        @keyframes flowBeam {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(350%); }
        }
        .flow-beam-active {
          position: absolute;
          top: 50%;
          left: 0;
          width: 80px;
          height: 2px;
          background: linear-gradient(90deg, transparent, #c084fc, transparent);
          animation: flowBeam 3s ease-in-out infinite;
        }
      `}</style>

      {/* Layer 0: Background Canvas & Atmospheric Effects */}
      <canvas
        ref={canvasRef}
        className="fixed inset-0 pointer-events-none opacity-40 z-0"
        style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0 }}
      />
      <div className="spotlight-overlay" />
      <div className="tech-grid" />
      <div className="falling-line line-1" />
      <div className="falling-line line-2" />
      <div className="falling-line line-3" />
      <div className="falling-line line-4" />
      <div className="falling-line line-5" />

      {/* =========================================================================
          SECTION 1 - NAVIGATION (Fixed top, backdrop-blur-xl, border-b border-white/5)
          ========================================================================= */}
      <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-[#020204]/75 border-b border-white/5 transition-all">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Left: Brand Logo */}
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center">
              <div className="absolute inset-0 bg-purple-600/40 blur-md rounded-lg" />
              <div className="relative w-8 h-8 rounded-lg bg-zinc-900 border border-white/10 flex items-center justify-center text-white">
                <Layers size={18} className="text-purple-400" />
              </div>
            </div>
            <span className="font-bold text-lg tracking-tight text-white flex items-center gap-1.5">
              EDGESTORE
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 font-mono font-medium">
                LUKS2
              </span>
            </span>
          </div>

          {/* Center: Navigation Links Pill */}
          <nav className="hidden md:flex items-center gap-1 px-4 py-1.5 rounded-full bg-white/[0.03] border border-white/10 text-xs font-medium text-slate-300">
            <a href="#platform" className="px-3 py-1 rounded-full hover:text-white hover:bg-white/5 transition-all">
              Platform
            </a>
            <a href="#security" className="px-3 py-1 rounded-full hover:text-white hover:bg-white/5 transition-all">
              Zero-Trust
            </a>
            <a href="#hardware" className="px-3 py-1 rounded-full hover:text-white hover:bg-white/5 transition-all">
              Hardware HAL
            </a>
            <a href="#metrics" className="px-3 py-1 rounded-full hover:text-white hover:bg-white/5 transition-all">
              Replication
            </a>
            <button
              onClick={() => setShowCredsModal(true)}
              className="px-3 py-1 rounded-full text-purple-300 hover:text-purple-200 hover:bg-purple-500/10 transition-all font-semibold"
            >
              Credentials
            </button>
          </nav>

          {/* Right: Search & Get Started CTA */}
          <div className="flex items-center gap-3">
            <div
              onClick={() => setShowCredsModal(true)}
              className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-md bg-white/[0.04] border border-white/10 text-[11px] text-slate-400 cursor-pointer hover:border-white/20 transition-all"
            >
              <Search size={12} />
              <span>Default Logins</span>
              <kbd className="px-1 py-0.5 text-[9px] rounded bg-white/10 text-slate-300 font-mono">CTRL+K</kbd>
            </div>

            <button
              onClick={onGetStarted}
              className="px-4 py-2 text-xs font-semibold rounded-full bg-white text-black hover:bg-zinc-200 transition-all flex items-center gap-1.5 shadow-[0_0_20px_rgba(255,255,255,0.15)] active:scale-95"
            >
              <span>{user ? "Enter Console" : "Get Started"}</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </header>

      {/* =========================================================================
          SECTION 2 - HERO (Newsreader font, md:text-8xl, Torus Knot, 3D Dashboard)
          ========================================================================= */}
      <section className="relative pt-32 pb-20 px-6 max-w-7xl mx-auto flex flex-col items-center text-center z-20">
        {/* Wireframe Spinning Torus Knot Visual (Tidiane Tambadou reference) */}
        <div className="absolute top-24 left-1/2 -translate-x-1/2 w-[480px] h-[480px] pointer-events-none opacity-20 -z-10 overflow-hidden">
          <svg viewBox="0 0 400 400" className="w-full h-full knot-container">
            {[0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150].map((deg) => (
              <ellipse
                key={deg}
                cx="200"
                cy="200"
                rx="140"
                ry="45"
                fill="none"
                stroke="#c084fc"
                strokeWidth="1"
                strokeDasharray={deg % 30 === 0 ? "4,4" : "none"}
                transform={`rotate(${deg} 200 200)`}
              />
            ))}
          </svg>
        </div>

        {/* Eyebrow Pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-medium mb-8">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500" />
          </span>
          <span>The Global Edge Storage Infrastructure for AI</span>
        </div>

        {/* Heading with Newsreader font */}
        <h1
          className="font-serif text-5xl sm:text-7xl md:text-8xl font-normal tracking-tight text-white max-w-5xl leading-[0.98] mb-6"
          style={{ fontFamily: "'Newsreader', Georgia, serif" }}
        >
          Scale beyond <br />
          <span className="italic bg-gradient-to-r from-white via-slate-200 to-slate-500 bg-clip-text text-transparent">
            the physical limits.
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-400 max-w-2xl font-light mb-10 leading-relaxed">
          Hardware-bound LUKS2 cryptographic storage built for autonomous edge nodes, Raspberry Pi 4, and resilient local vaults.
          Physical Key-SD security meets real-time dual-drive mirroring.
        </p>

        {/* CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-16">
          {/* Primary Conic-Glow Button */}
          <div className="btn-glow-border">
            <button
              onClick={onGetStarted}
              className="relative px-6 py-3 rounded-full bg-zinc-950 text-white font-medium text-sm hover:bg-zinc-900 transition-all flex items-center gap-2 z-10"
            >
              <span>{user ? "Open Console Dashboard" : "Get Started • Access Console"}</span>
              <ArrowRight size={15} className="text-purple-400" />
            </button>
          </div>

          <button
            onClick={() => setShowCredsModal(true)}
            className="px-6 py-3 rounded-full bg-white/[0.04] border border-white/10 text-slate-300 text-sm font-medium hover:bg-white/[0.08] hover:text-white transition-all flex items-center gap-2"
          >
            <ShieldCheck size={16} className="text-emerald-400" />
            <span>Default Credentials</span>
          </button>
        </div>

        {/* 3D Perspective Dashboard Preview (with Mini-Sidebar, Stat Grid, Scanline, and SVG Graph) */}
        <div className="w-full max-w-5xl dashboard-container">
          <div className="dashboard-card relative w-full bg-[#0a0a0f] border border-white/10 rounded-2xl p-4 sm:p-6 overflow-hidden text-left">
            <div className="scanline-bar" />

            {/* Dashboard Topbar */}
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/5">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
                <span className="ml-3 font-mono text-xs text-slate-500">edgestore-rpi4-node-01:~/vault</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  KEY-SD VERIFIED
                </span>
                <span className="text-xs text-slate-500 font-mono">LUKS2: ACTIVE</span>
              </div>
            </div>

            {/* Main Preview Body with Mini-Sidebar + Telemetry Grid */}
            <div className="flex gap-4">
              {/* Mini-Sidebar inside Dashboard Preview */}
              <div className="hidden sm:flex flex-col gap-1 w-36 pr-3 border-r border-white/5 font-mono text-[11px] text-slate-400">
                <div className="p-2 rounded bg-purple-500/15 text-purple-300 font-semibold flex items-center gap-2">
                  <Activity size={13} />
                  <span>Overview</span>
                </div>
                <div className="p-2 rounded hover:bg-white/5 flex items-center gap-2">
                  <FolderLock size={13} />
                  <span>File Vault</span>
                </div>
                <div className="p-2 rounded hover:bg-white/5 flex items-center gap-2">
                  <HardDrive size={13} />
                  <span>Volumes</span>
                </div>
                <div className="p-2 rounded hover:bg-white/5 flex items-center gap-2">
                  <RefreshCw size={13} />
                  <span>Mirror Sync</span>
                </div>
                <div className="p-2 rounded hover:bg-white/5 flex items-center gap-2">
                  <History size={13} />
                  <span>Audit Logs</span>
                </div>
              </div>

              {/* Right Content Area inside Dashboard Preview */}
              <div className="flex-1 min-w-0">
                {/* Metric Stat Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className="text-[11px] text-slate-500 mb-1 flex items-center gap-1">
                      <Database size={12} className="text-purple-400" />
                      Primary (A)
                    </div>
                    <div className="text-lg font-bold text-white font-mono">1.82 TB</div>
                    <div className="text-[10px] text-emerald-400 flex items-center gap-0.5 mt-0.5">
                      <ArrowUpRight size={10} /> ext4 clean
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className="text-[11px] text-slate-500 mb-1 flex items-center gap-1">
                      <Activity size={12} className="text-cyan-400" />
                      Replica (B)
                    </div>
                    <div className="text-lg font-bold text-white font-mono">1.82 TB</div>
                    <div className="text-[10px] text-emerald-400 flex items-center gap-0.5 mt-0.5">
                      <Check size={10} /> in-sync (0 lag)
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className="text-[11px] text-slate-500 mb-1 flex items-center gap-1">
                      <Zap size={12} className="text-yellow-400" />
                      Throughput
                    </div>
                    <div className="text-lg font-bold text-white font-mono">482 MB/s</div>
                    <div className="text-[10px] text-purple-400 flex items-center gap-0.5 mt-0.5">
                      AES-XTS-256
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className="text-[11px] text-slate-500 mb-1 flex items-center gap-1">
                      <Shield size={12} className="text-emerald-400" />
                      Security
                    </div>
                    <div className="text-lg font-bold text-white font-mono">100%</div>
                    <div className="text-[10px] text-slate-400 flex items-center gap-0.5 mt-0.5">
                      Rate-limit active
                    </div>
                  </div>
                </div>

                {/* SVG Graph Layer (Exact Adrino Labs coordinates) */}
                <div className="relative w-full h-36 rounded-xl bg-black/40 border border-white/5 overflow-hidden p-2">
                  <div className="absolute top-2.5 left-3 text-[11px] font-mono text-slate-400 flex items-center gap-2">
                    <span>IOPS TELEMETRY & DATA STREAMING</span>
                    <span className="text-[9px] text-purple-400 bg-purple-500/10 px-1.5 py-0.2 rounded font-semibold">
                      REALTIME
                    </span>
                  </div>
                  <svg viewBox="0 0 1000 300" className="w-full h-full preserve-3d" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="adrinoGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#a855f7" stopOpacity="0.38" />
                        <stop offset="100%" stopColor="#a855f7" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>
                    {/* Area Path */}
                    <path
                      d="M0 200 Q 100 180 200 150 T 400 160 T 600 100 T 800 80 T 1000 40 L 1000 300 L 0 300 Z"
                      fill="url(#adrinoGrad)"
                    />
                    {/* Stroke Path */}
                    <path
                      d="M0 200 Q 100 180 200 150 T 400 160 T 600 100 T 800 80 T 1000 40"
                      fill="none"
                      stroke="#c084fc"
                      strokeWidth="3.5"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 3 - DEVELOPER EXPERIENCE (Checklist & Syntax Code Window)
          ========================================================================= */}
      <section id="platform" className="relative py-24 px-6 max-w-7xl mx-auto z-20">
        <div className="flex flex-col lg:flex-row items-center gap-12">
          {/* Left Side: Checklist & Details */}
          <div className="lg:w-1/2 text-left">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium mb-4">
              <Code2 size={13} />
              <span>Developer-First Edge Appliance</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-6">
              Native REST APIs & Hardware-Level Control.
            </h2>
            <p className="text-slate-400 mb-8 leading-relaxed">
              Programmatically mount encrypted LUKS2 partitions, trigger semi-automated drive rebuilds, stream files with SHA-256
              verification, and subscribe to real-time telemetry over WebSockets.
            </p>

            <div className="space-y-4">
              <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
                <div className="p-1 rounded-md bg-emerald-500/10 text-emerald-400 mt-0.5">
                  <Check size={14} strokeWidth={3} />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Direct Physical Key-SD Interlock</h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Storage keys never persist on primary OS disk; they unlock exclusively when the physical SD card is inserted.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
                <div className="p-1 rounded-md bg-emerald-500/10 text-emerald-400 mt-0.5">
                  <Check size={14} strokeWidth={3} />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Sub-Millisecond Dual Mirroring</h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Atomic file transactions with asynchronous delta syncing to the secondary replica drive.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Side: Code Window with Syntax Highlighting */}
          <div className="lg:w-1/2 w-full">
            <div className="rounded-2xl bg-[#09090d] border border-white/10 shadow-2xl overflow-hidden text-left font-mono text-xs">
              {/* Code Window Header */}
              <div className="flex items-center justify-between px-4 py-3 bg-white/[0.02] border-b border-white/5">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
                  <span className="ml-2 text-slate-500">api_interlock.py</span>
                </div>
                <div className="flex gap-2 text-[11px]">
                  <button
                    onClick={() => setActiveTab("cli")}
                    className={`px-2 py-0.5 rounded ${activeTab === "cli" ? "bg-purple-500/20 text-purple-300" : "text-slate-500"}`}
                  >
                    CLI
                  </button>
                  <button
                    onClick={() => setActiveTab("python")}
                    className={`px-2 py-0.5 rounded ${activeTab === "python" ? "bg-purple-500/20 text-purple-300" : "text-slate-500"}`}
                  >
                    Python
                  </button>
                </div>
              </div>

              {/* Code Content */}
              <div className="p-5 overflow-x-auto leading-relaxed text-slate-300">
                {activeTab === "cli" ? (
                  <pre>
                    <code>
                      <span style={{ color: "#71717a" }}># Unlock appliance storage using hardware Key-SD</span>
                      {"\n"}
                      <span style={{ color: "#c084fc" }}>curl</span> -X POST https://edgestore.local/api/storage/unlock \{"\n"}
                      {"  "}-H <span style={{ color: "#34d399" }}>"Authorization: Bearer $APPLIANCE_TOKEN"</span> \{"\n"}
                      {"  "}-d <span style={{ color: "#34d399" }}>'{`{"passphrase": "HardwareVault2026!"}`}'</span>
                      {"\n\n"}
                      <span style={{ color: "#71717a" }}># Hardware Response</span>
                      {"\n"}
                      {`{`}
                      {"\n"}
                      {"  "}<span style={{ color: "#60a5fa" }}>"status"</span>: <span style={{ color: "#34d399" }}>"UNLOCKED"</span>,{"\n"}
                      {"  "}<span style={{ color: "#60a5fa" }}>"luks_device"</span>: <span style={{ color: "#34d399" }}>"/dev/mapper/edgestore_primary"</span>,{"\n"}
                      {"  "}<span style={{ color: "#60a5fa" }}>"replication"</span>: <span style={{ color: "#34d399" }}>"SYNCHRONIZED"</span>,{"\n"}
                      {"  "}<span style={{ color: "#60a5fa" }}>"integrity_sha256"</span>: <span style={{ color: "#34d399" }}>"VERIFIED_OK"</span>
                      {"\n"}
                      {`}`}
                    </code>
                  </pre>
                ) : (
                  <pre>
                    <code>
                      <span style={{ color: "#c084fc" }}>import</span> edgestore{"\n\n"}
                      client = edgestore.<span style={{ color: "#60a5fa" }}>Client</span>(endpoint=<span style={{ color: "#34d399" }}>"http://127.0.0.1:8000"</span>){"\n"}
                      <span style={{ color: "#71717a" }}># Upload payload with end-to-end SHA-256 hash</span>{"\n"}
                      receipt = client.files.<span style={{ color: "#60a5fa" }}>upload</span>({"\n"}
                      {"    "}file_path=<span style={{ color: "#34d399" }}>"critical_telemetry.tar.gz"</span>,{"\n"}
                      {"    "}encrypt_luks2=<span style={{ color: "#c084fc" }}>True</span>,{"\n"}
                      {"    "}mirror_replica=<span style={{ color: "#c084fc" }}>True</span>{"\n"}
                      ){"\n"}
                      <span style={{ color: "#60a5fa" }}>print</span>(f<span style={{ color: "#34d399" }}>"Stored: {'{receipt.file_id}'} SHA-256: {'{receipt.sha256}'}"</span>)
                    </code>
                  </pre>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 4 - BENTO FEATURES (6-column grid)
          ========================================================================= */}
      <section id="security" className="relative py-20 px-6 max-w-7xl mx-auto z-20 text-left">
        <div className="mb-12">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-medium mb-3">
            <BoxSelect size={13} />
            <span>Architecture & Defense</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Engineered for physical hostility.
          </h2>
        </div>

        {/* 6-Column Grid */}
        <div className="grid grid-cols-1 md:grid-cols-6 gap-6">
          {/* Card 1 (4 cols): Global Edge Mesh */}
          <div className="md:col-span-4 p-6 sm:p-8 rounded-2xl bg-[#09090d] border border-white/10 relative overflow-hidden flex flex-col justify-between">
            <div className="relative z-10">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4">
                <Globe size={20} />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Hardware-Bound Storage Interlock</h3>
              <p className="text-sm text-slate-400 max-w-md">
                Encrypted with LUKS2 AES-XTS-PLAIN64. If the device is stolen or powered off, drives are cryptographically unreadable without the physical Key-SD.
              </p>
            </div>

            {/* Pulse Node Visual */}
            <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-between text-xs font-mono text-slate-500">
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping" />
                <span>ACTIVE NODES: 2 (PRIMARY + REPLICA)</span>
              </div>
              <span className="text-emerald-400">ENCRYPTION: HARDWARE AES</span>
            </div>
          </div>

          {/* Card 2 (2 cols): Zero Trust */}
          <div className="md:col-span-2 p-6 sm:p-8 rounded-2xl bg-[#09090d] border border-white/10 relative flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
                <ShieldCheck size={20} />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Zero-Trust RBAC</h3>
              <p className="text-xs text-slate-400 mb-6">
                35 granular capabilities. Server-side session invalidation and IP brute-force rate-limiting.
              </p>
            </div>

            {/* Pass/Active List */}
            <div className="space-y-2 font-mono text-[11px]">
              <div className="flex items-center justify-between p-2 rounded bg-white/[0.02] border border-white/5">
                <span className="text-slate-400">Rate Limiter</span>
                <span className="text-emerald-400 font-bold">PASS</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-white/[0.02] border border-white/5">
                <span className="text-slate-400">IDOR Ownership</span>
                <span className="text-emerald-400 font-bold">PASS</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-white/[0.02] border border-white/5">
                <span className="text-slate-400">Path Traversal</span>
                <span className="text-emerald-400 font-bold">BLOCKED</span>
              </div>
            </div>
          </div>

          {/* Card 3 (3 cols): Real-Time Metrics */}
          <div className="md:col-span-3 p-6 sm:p-8 rounded-2xl bg-[#09090d] border border-white/10 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
                <BarChart2 size={20} />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Real-Time IOPS Telemetry</h3>
              <p className="text-xs text-slate-400 mb-6">
                Direct hardware sensor polling for temperature, throttling, and storage bus latency.
              </p>
            </div>

            {/* Metric Bars */}
            <div className="flex items-end gap-2 h-20 w-full pt-4">
              {[40, 65, 30, 85, 95, 70, 80, 100, 60, 75, 90, 85].map((val, idx) => (
                <div key={idx} className="flex-1 bg-cyan-950/60 rounded-t relative group overflow-hidden">
                  <div
                    className="w-full bg-cyan-400 rounded-t transition-all duration-500 group-hover:bg-cyan-300"
                    style={{ height: `${val}%` }}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Card 4 (3 cols): Instant Rollbacks / Rebuilds */}
          <div className="md:col-span-3 p-6 sm:p-8 rounded-2xl bg-[#09090d] border border-white/10 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-xl bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center text-yellow-400">
                  <GitBranch size={20} />
                </div>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-white/5 text-slate-300 border border-white/10">
                  v2.4.1 (Stable)
                </span>
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Semi-Automated Rebuild</h3>
              <p className="text-xs text-slate-400 mb-6">
                Replace a degraded drive with zero downtime. Formats LUKS2 container and mirrors sector deltas automatically.
              </p>
            </div>

            <button
              onClick={onGetStarted}
              className="w-full py-2.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-white transition-all flex items-center justify-center gap-2"
            >
              <span>Inspect Drive Health</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 5 - ONBOARDING (Three-step pipeline with shared flow-beam)
          ========================================================================= */}
      <section id="hardware" className="relative py-24 px-6 max-w-7xl mx-auto z-20 text-center">
        <div className="max-w-xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-medium mb-3">
            <Sparkles size={13} />
            <span>Zero-Friction Deployment</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-3">
            Three steps to hardened edge storage.
          </h2>
          <p className="text-slate-400 text-sm">
            From bare-metal Raspberry Pi 4 to production-grade replicated file vault in under 60 seconds.
          </p>
        </div>

        {/* 3 Step Cards with Flow-Beam connecting animation */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          <div className="hidden md:block flow-beam-active" />

          {/* Step 1 */}
          <div className="p-6 rounded-2xl bg-[#09090d] border border-white/10 text-left relative">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 font-mono font-bold text-sm flex items-center justify-center mb-4">
              01
            </div>
            <h4 className="text-base font-bold text-white mb-2">Provision Physical Key-SD</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Format removable SD with high-entropy cryptographic token. Insert into node slot.
            </p>
            <div className="mt-4 p-2.5 rounded bg-black/50 border border-white/5 font-mono text-[11px] text-slate-400 flex items-center gap-2">
              <Terminal size={12} className="text-purple-400" />
              <span>edgestore init --key-sd</span>
            </div>
          </div>

          {/* Step 2 */}
          <div className="p-6 rounded-2xl bg-[#09090d] border border-white/10 text-left relative">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 font-mono font-bold text-sm flex items-center justify-center mb-4">
              02
            </div>
            <h4 className="text-base font-bold text-white mb-2">Attach Storage Drives</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Connect dual USB 3.0 SSD/HDDs. EdgeStore auto-detects and formats LUKS2 containers.
            </p>
            <div className="mt-4 p-2.5 rounded bg-black/50 border border-white/5 font-mono text-[11px] text-slate-400 flex items-center gap-2">
              <Cpu size={12} className="text-cyan-400" />
              <span>Drive A + B: Ready</span>
            </div>
          </div>

          {/* Step 3 */}
          <div className="p-6 rounded-2xl bg-[#09090d] border border-white/10 text-left relative">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 font-mono font-bold text-sm flex items-center justify-center mb-4">
              03
            </div>
            <h4 className="text-base font-bold text-white mb-2">Sign in & Orchestrate</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Use enterprise RBAC roles (Super Admin, Storage Operator, Guest) to control appliance.
            </p>
            <div className="mt-4 p-2.5 rounded bg-black/50 border border-white/5 font-mono text-[11px] text-slate-400 flex items-center gap-2">
              <Globe2 size={12} className="text-emerald-400" />
              <span>https://127.0.0.1:8000/</span>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 6 - FINAL CTA & FOOTER (Massive card, ripples, social links)
          ========================================================================= */}
      <section className="relative py-20 px-6 max-w-7xl mx-auto z-20">
        {/* Massive Call-to-Action Card with Concentric Ripple Borders */}
        <div className="relative rounded-3xl bg-gradient-to-b from-[#12121c] to-[#08080c] border border-white/15 p-12 sm:p-16 text-center overflow-hidden shadow-2xl">
          {/* Concentric Ripple Rings */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] rounded-full border border-purple-500/10 pointer-events-none" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[750px] h-[750px] rounded-full border border-purple-500/5 pointer-events-none" />
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 bg-purple-600/20 rounded-full blur-[100px] pointer-events-none" />

          <h2
            className="font-serif text-4xl sm:text-6xl font-normal text-white tracking-tight mb-4 max-w-2xl mx-auto leading-tight"
            style={{ fontFamily: "'Newsreader', Georgia, serif" }}
          >
            Ready to secure your edge?
          </h2>
          <p className="text-slate-400 text-base max-w-lg mx-auto mb-8 font-light">
            Deploy hardware-bound LUKS2 storage with real-time replication in minutes.
          </p>

          <button
            onClick={onGetStarted}
            className="px-8 py-3.5 rounded-full bg-white text-black font-bold text-sm hover:bg-zinc-200 transition-all shadow-[0_0_30px_rgba(255,255,255,0.2)] active:scale-95 inline-flex items-center gap-2"
          >
            <span>{user ? "Enter Console Dashboard" : "Get Started • Access Console"}</span>
            <ArrowRight size={15} />
          </button>
        </div>

        {/* Footer */}
        <footer className="mt-20 pt-12 border-t border-white/5 text-xs text-slate-500">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 text-left mb-12">
            <div className="col-span-2">
              <div className="flex items-center gap-2 text-white font-bold text-base mb-3">
                <Layers size={18} className="text-purple-400" />
                <span>EDGESTORE</span>
              </div>
              <p className="text-slate-400 max-w-sm mb-4 leading-relaxed">
                Secure edge storage appliance prototype designed for Raspberry Pi 4 with physical Key-SD authentication,
                LUKS2 disk encryption, and dual-drive replication.
              </p>
              <div className="flex items-center gap-3 text-slate-400">
                <a href="https://x.com" target="_blank" rel="noreferrer" className="p-2 rounded-lg bg-white/5 hover:text-white transition-all" title="X / Twitter">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                </a>
                <a href="https://github.com" target="_blank" rel="noreferrer" className="p-2 rounded-lg bg-white/5 hover:text-white transition-all" title="GitHub">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
                </a>
                <a href="https://linkedin.com" target="_blank" rel="noreferrer" className="p-2 rounded-lg bg-white/5 hover:text-white transition-all" title="LinkedIn">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.24a1.66 1.66 0 0 0-1.66 1.66 1.66 1.66 0 0 0 1.66 1.66 1.66 1.66 0 0 0 1.66-1.66 1.66 1.66 0 0 0-1.66-1.66Z"/></svg>
                </a>
              </div>
            </div>

            <div>
              <h5 className="text-white font-semibold mb-3">Product</h5>
              <ul className="space-y-2">
                <li><a href="#platform" className="hover:text-slate-300">Architecture</a></li>
                <li><a href="#security" className="hover:text-slate-300">Zero Trust</a></li>
                <li><a href="#hardware" className="hover:text-slate-300">Hardware HAL</a></li>
                <li><a href="#metrics" className="hover:text-slate-300">Replication</a></li>
              </ul>
            </div>

            <div>
              <h5 className="text-white font-semibold mb-3">Resources</h5>
              <ul className="space-y-2">
                <li><a href="#" onClick={onGetStarted} className="hover:text-slate-300">Console Login</a></li>
                <li><button onClick={() => setShowCredsModal(true)} className="hover:text-slate-300">Default Credentials</button></li>
                <li><a href="#" className="hover:text-slate-300">API Documentation</a></li>
                <li><a href="#" className="hover:text-slate-300">Security Model</a></li>
              </ul>
            </div>

            <div>
              <h5 className="text-white font-semibold mb-3">Appliance</h5>
              <ul className="space-y-2">
                <li><span className="text-slate-400">Node: RPi 4 Model B</span></li>
                <li><span className="text-slate-400">Kernel: Linux 6.6</span></li>
                <li><span className="text-slate-400">Storage: LUKS2 AES</span></li>
                <li><span className="text-emerald-400">Status: Operational</span></li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between pt-6 border-t border-white/5 gap-4">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-slate-400">All EdgeStore Systems Operational</span>
            </div>
            <div>
              © 2026 EdgeStore Appliance • Defense-in-Depth Hardware Edition
            </div>
          </div>
        </footer>
      </section>

      {/* Horizon Ring for perspective finish */}
      <div className="horizon-ring" />

      {/* =========================================================================
          INTERACTIVE DEFAULT CREDENTIALS MODAL (Requested explicitly by user)
          ========================================================================= */}
      {showCredsModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 100,
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            backdropFilter: "blur(8px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 20,
          }}
          onClick={() => setShowCredsModal(false)}
        >
          <div
            style={{
              width: "100%",
              maxWidth: 480,
              backgroundColor: "#09090d",
              border: "1px solid #27272a",
              borderRadius: 16,
              padding: 28,
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.9)",
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ p: 6, borderRadius: 8, backgroundColor: "rgba(168, 85, 247, 0.15)", color: "#c084fc", display: "flex" }}>
                  <ShieldCheck size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff", margin: 0 }}>Default Credentials</h3>
                  <p style={{ fontSize: 12, color: "#71717a", margin: 0 }}>Pre-configured appliance testing accounts</p>
                </div>
              </div>
              <button
                onClick={() => setShowCredsModal(false)}
                style={{ background: "none", border: "none", color: "#71717a", cursor: "pointer" }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {/* Super Admin */}
              <div
                style={{
                  padding: 14,
                  borderRadius: 10,
                  backgroundColor: "#121216",
                  border: "1px solid #1f1f26",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "#ffffff" }}>Super Administrator</span>
                  <span style={{ fontSize: 10, color: "#a855f7", backgroundColor: "rgba(168, 85, 247, 0.15)", padding: "2px 6px", borderRadius: 4, fontFamily: "monospace" }}>
                    super_admin
                  </span>
                </div>
                <div style={{ fontSize: 12, color: "#94a3b8", fontFamily: "monospace", marginBottom: 8 }}>
                  Username: <strong style={{ color: "#ffffff" }}>admin</strong> • Password: <strong style={{ color: "#ffffff" }}>AdminEdgeStore2026!</strong>
                </div>
                <button
                  onClick={() => {
                    setShowCredsModal(false);
                    onGetStarted();
                  }}
                  style={{
                    width: "100%",
                    padding: "6px 0",
                    fontSize: 11,
                    fontWeight: 600,
                    borderRadius: 6,
                    backgroundColor: "#ffffff",
                    color: "#000000",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  Launch Console as Admin
                </button>
              </div>

              {/* Storage Operator */}
              <div
                style={{
                  padding: 14,
                  borderRadius: 10,
                  backgroundColor: "#121216",
                  border: "1px solid #1f1f26",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "#ffffff" }}>Storage Operator</span>
                  <span style={{ fontSize: 10, color: "#38bdf8", backgroundColor: "rgba(56, 189, 248, 0.15)", padding: "2px 6px", borderRadius: 4, fontFamily: "monospace" }}>
                    storage_admin
                  </span>
                </div>
                <div style={{ fontSize: 12, color: "#94a3b8", fontFamily: "monospace", marginBottom: 8 }}>
                  Username: <strong style={{ color: "#ffffff" }}>operator</strong> • Password: <strong style={{ color: "#ffffff" }}>OperatorEdgeStore2026!</strong>
                </div>
                <button
                  onClick={() => {
                    setShowCredsModal(false);
                    onGetStarted();
                  }}
                  style={{
                    width: "100%",
                    padding: "6px 0",
                    fontSize: 11,
                    fontWeight: 600,
                    borderRadius: 6,
                    backgroundColor: "#27272a",
                    color: "#ffffff",
                    border: "1px solid #3f3f46",
                    cursor: "pointer",
                  }}
                >
                  Launch Console as Operator
                </button>
              </div>

              {/* Guest Viewer */}
              <div
                style={{
                  padding: 14,
                  borderRadius: 10,
                  backgroundColor: "#121216",
                  border: "1px solid #1f1f26",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "#ffffff" }}>Project Reviewer (Guest)</span>
                  <span style={{ fontSize: 10, color: "#4ade80", backgroundColor: "rgba(74, 222, 128, 0.15)", padding: "2px 6px", borderRadius: 4, fontFamily: "monospace" }}>
                    guest
                  </span>
                </div>
                <div style={{ fontSize: 12, color: "#94a3b8", fontFamily: "monospace", marginBottom: 8 }}>
                  Username: <strong style={{ color: "#ffffff" }}>guest</strong> • Password: <strong style={{ color: "#ffffff" }}>GuestEdgeStore2026!</strong>
                </div>
                <button
                  onClick={() => {
                    setShowCredsModal(false);
                    onGetStarted();
                  }}
                  style={{
                    width: "100%",
                    padding: "6px 0",
                    fontSize: 11,
                    fontWeight: 600,
                    borderRadius: 6,
                    backgroundColor: "#27272a",
                    color: "#ffffff",
                    border: "1px solid #3f3f46",
                    cursor: "pointer",
                  }}
                >
                  Launch Console as Guest
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
