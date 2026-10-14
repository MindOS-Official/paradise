# Mind Helper — Design System & Architecture Specification

## Identity & Voice
- **Name**: Mind Helper
- **Persona**: An intelligent, cerebral, chillingly polite Linux companion and tutor. Speaks with quiet respect, precision, and calm depth. Never frantic, never patronizing.
- **Role**: Explains and teaches Linux, monitors system vitals, diagnoses issues, answers queries, and inspects community feedback.

## Visual Direction
- **Theme**: Celestial Obsidian & Cold Slate.
- **Palette**:
  - Background Neutral: `#090d16` (Deep Space Obsidian) / `#0f172a` (Night Slate)
  - Card Surfaces: `#131b2e` with subtle `#1e293b` borders (matte, solid, high contrast)
  - Accent Color: `#38bdf8` (Celestial Cyan) & `#818cf8` (Gemini Violet Accent)
  - Text Primary: `#f8fafc` (Slate 50)
  - Text Secondary: `#94a3b8` (Slate 400)
  - Error/Blocked: `#f43f5e` (Rose)
  - Success/Approved: `#34d399` (Emerald)
- **Typography**: Clean system sans-serif (Ubuntu, Cantarell, Inter, system-ui) paired with Monospace (`monospace`, `Fira Code`) for commands and shell outputs.
- **Animation Motif**: Google Gemini 4-point astroid star (`✦`), subtle celestial gradient rotation, and shimmering glow line when thinking or computing.

## Dials
- **ENERGY**: 2 (Calm, cerebral, focused).
- **RHYTHM**: 2 (Varied cards and tabs tailored to their functional content).
- **MOTION**: 2 (Smooth Cairo-rendered 4-point star rotation and shimmer, active only when computing; zero idle CPU drain).

## Purpose Test
- Every UI element serves a concrete purpose:
  - Minimized dock: Immediate, glanceable RAM, weather, and uptime telemetry with zero clutter.
  - Quick Question bar in minimized dock: Rapid access to Linux knowledge without disrupting workflow.
  - Tutorials tab: Structured curriculum for learning Linux hands-on with copyable commands.
  - Feedback tab: Enforces strict 24h cadence, inspects content for appropriateness, and dispatches to the developer privately.
