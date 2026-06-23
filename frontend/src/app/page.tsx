"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

const DEMO_LINES = [
  { delay: 0,    text: '> searching 2.4M candidate profiles...',    color: '#6B7280' },
  { delay: 600,  text: '✓ vector index queried in 38ms',            color: '#F59E0B' },
  { delay: 1100, text: '✓ 847 semantic matches found',              color: '#F59E0B' },
  { delay: 1700, text: '> running ML ranking pipeline...',          color: '#6B7280' },
  { delay: 2300, text: '✓ XGBoost scores computed',                 color: '#F59E0B' },
  { delay: 2800, text: '',                                           color: '' },
  { delay: 2900, text: '─── top match ───────────────────',         color: '#374151' },
  { delay: 3000, text: 'Priya Sharma  •  Sr. ML Engineer',          color: '#F1F5F9' },
  { delay: 3200, text: 'Match score    ████████░░  82%',            color: '#F59E0B' },
  { delay: 3400, text: 'Skills         Python · PyTorch · AWS',     color: '#94A3B8' },
  { delay: 3600, text: 'Experience     6 yrs  •  ₹28L current',     color: '#94A3B8' },
  { delay: 3800, text: 'Notice period  30 days',                    color: '#94A3B8' },
  { delay: 4200, text: '',                                           color: '' },
  { delay: 4300, text: '> 2 more top-tier candidates ready ↓',      color: '#6B7280' },
];

function TerminalCard() {
  const [visibleCount, setVisibleCount] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    DEMO_LINES.forEach((line, i) => {
      setTimeout(() => setVisibleCount(i + 1), line.delay);
    });
  }, []);

  return (
    <div style={{
      background: '#0D1117',
      border: '1px solid #1E2A3A',
      borderRadius: '12px',
      fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
      fontSize: '12.5px',
      lineHeight: '1.7',
      overflow: 'hidden',
      boxShadow: '0 0 0 1px rgba(245,158,11,0.06), 0 24px 48px rgba(0,0,0,0.5)',
    }}>
      {/* titlebar */}
      <div style={{
        background: '#161B22',
        borderBottom: '1px solid #1E2A3A',
        padding: '10px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}>
        <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#FF5F57', display: 'inline-block' }} />
        <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#FEBC2E', display: 'inline-block' }} />
        <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#28C840', display: 'inline-block' }} />
        <span style={{ marginLeft: 8, color: '#4B5563', fontSize: '11px', letterSpacing: '0.05em' }}>redrob — candidate-discovery</span>
      </div>

      {/* output */}
      <div style={{ padding: '18px 20px', minHeight: '260px' }}>
        {DEMO_LINES.slice(0, visibleCount).map((line, i) => (
          <div key={i} style={{ color: line.color, whiteSpace: 'pre' }}>
            {line.text}
          </div>
        ))}
        {visibleCount < DEMO_LINES.length && (
          <span style={{
            display: 'inline-block',
            width: '8px',
            height: '14px',
            background: '#F59E0B',
            animation: 'blink 1s step-end infinite',
            verticalAlign: 'text-bottom',
          }} />
        )}
      </div>
    </div>
  );
}

const STATS = [
  { value: '2.4M', label: 'Profiles indexed' },
  { value: '<40ms', label: 'Avg. retrieval' },
  { value: '91%', label: 'Ranking accuracy' },
  { value: '8×', label: 'Faster than manual' },
];

export default function Home() {
  return (
    <div style={{
      minHeight: '100vh',
      background: '#0c0d12',
      color: '#f1f5f9',
      fontFamily: '"Inter", system-ui, -apple-system, sans-serif',
      position: 'relative',
      overflowX: 'hidden',
    }}>
      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        .hero-left { animation: fadeUp 0.6s ease both; }
        .hero-right { animation: fadeUp 0.6s 0.2s ease both; }
        .stat-item { animation: fadeUp 0.5s ease both; }
        .stat-item:nth-child(1){animation-delay:0.4s}
        .stat-item:nth-child(2){animation-delay:0.5s}
        .stat-item:nth-child(3){animation-delay:0.6s}
        .stat-item:nth-child(4){animation-delay:0.7s}
        .feature-card:hover { border-color: rgba(245,158,11,0.3) !important; }
        .cta-primary:hover { background: #D97706 !important; }
        .cta-secondary:hover { border-color: #4B5563 !important; color: #F1F5F9 !important; }
        @media(max-width:900px){
          .hero-grid { flex-direction: column !important; }
          .hero-right { display: none !important; }
          .stats-row { grid-template-columns: repeat(2,1fr) !important; }
        }
      `}</style>

      {/* Subtle grid texture */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0,
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.02) 1px,transparent 1px)',
        backgroundSize: '48px 48px',
        pointerEvents: 'none',
      }} />

      {/* Amber glow — top right only */}
      <div style={{
        position: 'fixed', top: '-20%', right: '-10%',
        width: '600px', height: '600px',
        background: 'radial-gradient(circle, rgba(245,158,11,0.06) 0%, transparent 70%)',
        zIndex: 0, pointerEvents: 'none',
      }} />

      {/* Nav */}
      <nav style={{
        position: 'relative', zIndex: 10,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '20px 56px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <rect x="1" y="1" width="20" height="20" rx="5" fill="#F59E0B" />
            <path d="M6 15l4-8 3 5 2-3 1 2" stroke="#0D1117" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span style={{ fontWeight: 700, fontSize: '15px', letterSpacing: '-0.02em', color: '#F1F5F9' }}>
            Redrob Discovery
          </span>
        </div>

        <div style={{ display: 'flex', gap: '32px', fontSize: '13px', color: '#6B7280' }}>
          <Link href="/dashboard" style={{ color: '#6B7280', textDecoration: 'none' }}>Dashboard</Link>
          <a href="#" style={{ color: '#6B7280', textDecoration: 'none' }}>Docs</a>
          <a href="#" style={{ color: '#6B7280', textDecoration: 'none' }}>API</a>
        </div>

        <Link
          href="/dashboard"
          style={{
            background: '#F59E0B',
            color: '#0D1117',
            fontWeight: 600,
            fontSize: '13px',
            padding: '8px 18px',
            borderRadius: '8px',
            textDecoration: 'none',
            letterSpacing: '-0.01em',
          }}
          className="cta-primary"
        >
          Open workspace →
        </Link>
      </nav>

      {/* Hero */}
      <div style={{
        position: 'relative', zIndex: 10,
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '72px 56px 80px',
        display: 'flex',
        alignItems: 'center',
        gap: '64px',
      }} className="hero-grid">

        {/* Left */}
        <div style={{ flex: '1 1 0', minWidth: 0 }} className="hero-left">
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '8px',
            background: 'rgba(245,158,11,0.1)',
            border: '1px solid rgba(245,158,11,0.2)',
            borderRadius: '20px',
            padding: '5px 14px',
            fontSize: '11px',
            fontWeight: 600,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: '#F59E0B',
            marginBottom: '28px',
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#F59E0B', display: 'inline-block', animation: 'blink 2s step-end infinite' }} />
            AI-Powered Candidate Intelligence
          </div>

          <h1 style={{
            fontSize: 'clamp(36px, 5vw, 56px)',
            fontWeight: 800,
            letterSpacing: '-0.04em',
            lineHeight: 1.1,
            margin: '0 0 24px',
            color: '#F1F5F9',
          }}>
            Find the right hire<br />
            <span style={{ color: '#F59E0B' }}>in minutes,</span><br />
            not weeks.
          </h1>

          <p style={{
            fontSize: '17px',
            lineHeight: 1.7,
            color: '#64748B',
            maxWidth: '480px',
            margin: '0 0 40px',
          }}>
            Redrob Discovery searches millions of candidate profiles using vector similarity and ML ranking — so you spend your time on conversations, not spreadsheets.
          </p>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <Link
              href="/dashboard"
              id="enter-dashboard-cta"
              style={{
                background: '#F59E0B',
                color: '#0D1117',
                fontWeight: 700,
                fontSize: '14px',
                padding: '14px 28px',
                borderRadius: '10px',
                textDecoration: 'none',
                letterSpacing: '-0.01em',
                display: 'inline-flex', alignItems: 'center', gap: '8px',
              }}
              className="cta-primary"
            >
              Enter recruiter workspace
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 7h8M7 3l4 4-4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Link>

            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              style={{
                background: 'transparent',
                border: '1px solid #1E293B',
                color: '#94A3B8',
                fontWeight: 500,
                fontSize: '14px',
                padding: '14px 24px',
                borderRadius: '10px',
                textDecoration: 'none',
              }}
              className="cta-secondary"
            >
              System documentation
            </a>
          </div>
        </div>

        {/* Right — terminal */}
        <div style={{ flex: '0 0 420px', maxWidth: '420px' }} className="hero-right">
          <TerminalCard />
        </div>
      </div>

      {/* Stats bar */}
      <div style={{
        position: 'relative', zIndex: 10,
        borderTop: '1px solid rgba(255,255,255,0.04)',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
        background: 'rgba(255,255,255,0.02)',
      }}>
        <div style={{
          maxWidth: '1200px', margin: '0 auto', padding: '0 56px',
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
        }} className="stats-row">
          {STATS.map((s, i) => (
            <div key={i} className="stat-item" style={{
              padding: '28px 24px',
              borderRight: i < 3 ? '1px solid rgba(255,255,255,0.04)' : 'none',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '28px', fontWeight: 800, letterSpacing: '-0.04em', color: '#F1F5F9', lineHeight: 1.1 }}>{s.value}</div>
              <div style={{ fontSize: '12px', color: '#4B5563', marginTop: '4px', letterSpacing: '0.02em' }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Feature cards */}
      <div style={{
        position: 'relative', zIndex: 10,
        maxWidth: '1200px', margin: '0 auto',
        padding: '72px 56px 96px',
      }}>
        <div style={{
          fontSize: '11px', fontWeight: 600, letterSpacing: '0.1em',
          textTransform: 'uppercase', color: '#4B5563',
          marginBottom: '40px',
        }}>
          How it works
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1px', background: 'rgba(255,255,255,0.04)', borderRadius: '12px', overflow: 'hidden' }}>
          {[
            {
              icon: (
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <circle cx="9" cy="9" r="6" stroke="#F59E0B" strokeWidth="1.5" />
                  <path d="M13.5 13.5l3 3" stroke="#F59E0B" strokeWidth="1.8" strokeLinecap="round" />
                </svg>
              ),
              label: '01',
              title: 'Semantic search',
              body: 'Describe the role in plain English. The system converts it into a vector query and retrieves candidates by meaning, not just keywords.',
            },
            {
              icon: (
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <rect x="3" y="13" width="3" height="4" rx="1" fill="#F59E0B" />
                  <rect x="8.5" y="9" width="3" height="8" rx="1" fill="#F59E0B" opacity=".6" />
                  <rect x="14" y="5" width="3" height="12" rx="1" fill="#F59E0B" opacity=".3" />
                </svg>
              ),
              label: '02',
              title: 'ML ranking',
              body: 'Shortlisted candidates are re-ranked by experience overlap, skills fit, expected salary, and notice period — scored in real time.',
            },
            {
              icon: (
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M4 10h12M10 4l6 6-6 6" stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              ),
              label: '03',
              title: 'Explainable results',
              body: 'Every score comes with a plain-language breakdown — why this candidate ranks high, and which gaps to watch for before interviewing.',
            },
          ].map((f, i) => (
            <div key={i} className="feature-card" style={{
              background: '#0A0F1A',
              padding: '32px 28px',
              border: '1px solid transparent',
              transition: 'border-color 0.2s',
              cursor: 'default',
            }}>
              <div style={{ marginBottom: '20px' }}>{f.icon}</div>
              <div style={{ fontSize: '11px', color: '#374151', fontWeight: 600, letterSpacing: '0.08em', marginBottom: '8px' }}>{f.label}</div>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#E2E8F0', letterSpacing: '-0.02em', margin: '0 0 10px' }}>{f.title}</h3>
              <p style={{ fontSize: '13px', color: '#475569', lineHeight: 1.7, margin: 0 }}>{f.body}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer stripe */}
      <div style={{
        position: 'relative', zIndex: 10,
        borderTop: '1px solid rgba(255,255,255,0.04)',
        padding: '24px 56px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        maxWidth: '1200px', margin: '0 auto',
      }}>
        <span style={{ fontSize: '12px', color: '#374151' }}>© 2024 Redrob Discovery · AI-Powered Candidate Intelligence</span>
        <span style={{ fontSize: '12px', color: '#374151' }}>Powered by dense vector embeddings + XGBoost</span>
      </div>
    </div>
  );
}