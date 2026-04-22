# Pedagogica — Non-Goals (Artifact 6)

Status: Final planning artifact. Reviewed against Artifacts 1–5.

This document exists because every appealing feature we could build is an appealing feature we *won't* build — not yet, or ever. Naming non-goals protects focus, protects the schedule, and protects the definition of the product.

A non-goal is one of two things: **Permanent** (we are never building this) or **Deferred past Phase N** (in scope later, not now). The list below is small on purpose. Every item has been through Artifact 1's confirmation pass.

---

## 1. Permanent non-goals

Things we will not build, full stop. Revisiting any of these requires reopening this document and a deliberate decision.

### 1.1 Generative-video-based content for core pedagogy

**Meaning.** No Sora, Veo, Runway, Kling, Pika, or successor video-generation model is used to produce the core educational content of a video.

**Why permanent.** Generative video models cannot produce consistent equations, handwriting, notation, or diagrams across a long video. This constraint is the architectural reason Pedagogica exists — if generative video becomes reliable for equations and diagrams at a later date, we reopen this decision, but the product today is defined by the opposite bet.

**What remains open.** B-roll (stock footage of the solar system, a spinning planet, an atom vibrating) via generative video is acceptable in Phase 5+ as supplemental material, never as the pedagogical core.

### 1.2 Live classroom tools

**Meaning.** We do not build real-time whiteboard tools, live-interaction student software, simultaneous-presence classroom apps, or anything where an educator and students are both online at the same moment.

**Why permanent.** Pedagogica is an asset-generation product — we make videos that are watched asynchronously. Live classroom software is a different product (Zoom, Classroom) and a different discipline (real-time distributed systems, multi-user sync). Mixing the two dilutes both.

### 1.3 Human-in-the-loop lipsyncing / avatar anchors

**Meaning.** We do not produce videos where a photorealistic or cartoon avatar speaks to camera with generated lipsync.

**Why permanent.** The style we target (3B1B, Khan, Veritasium-animations-segment) is voice-over on illustration, not presenter-to-camera. Adding avatars would be a categorically different product. If a creator wants a talking-head, they shoot themselves; we supply the animation they cut to.

### 1.4 Reading student-submitted work

**Meaning.** We do not ingest student essays, homework, scanned notes, or problem sets as input to tailor content.

**Why permanent.** Student-data ingestion unlocks FERPA / GDPR / child-data-protection compliance costs that a greenfield project can't pay without funding. Educational-institution integration (if we want it) is Phase 6 and handled via an LMS-level partner that owns that compliance.

### 1.5 Content moderation and reporting infrastructure

**Meaning.** We rely on the underlying LLM's safety (Anthropic's baseline). We do not build community reporting, human review queues, content flagging systems, appeals processes, or editorial policies beyond that.

**Why permanent for single-user Phase 1–3.** Pedagogica in Phase 1–3 is single-user — Rachit is the only person using it. Phase 4 adds external users, and from Phase 4 the operative safety mechanism is still Anthropic's baseline plus prompt-level refusals for high-stakes domains (medical dosing, legal advice, self-harm). We do not build YouTube's or Reddit's moderation apparatus. If the product needs that to succeed, we've mis-scoped the customer.

### 1.6 Relitigating the renderer bet

**Meaning.** The architectural decision on which code the LLM generates for the visual primitive is not on the table for mid-phase debate.

**History.** The bet originally named Manim Community Edition 0.19.x. On 2026-04-21 that bet was superseded by ADR 0001: **chalk** (this repo's own renderer under `chalk/`) replaced MCE as the primitive. The decision, rationale, kill criteria (K1–K5), and reversion plan are captured there. This was an explicit, documented renderer change — not a drift.

**What stays permanent.** No further mid-phase renderer debates (chalk vs MCE vs Remotion vs Motion Canvas vs raw SVG) are in scope until one of ADR 0001's kill criteria fires. If K1–K5 fire, the reversion plan in the ADR is the path back to MCE; a *different* renderer choice requires a fresh ADR.

**Why permanent for the next 40 weeks.** The foundational bet is still "own the renderer we generate for." Which specific renderer implements that bet is answered by ADR 0001 and can only be reopened through the kill criteria, not vibes. Mid-phase debates waste time either way.

---

## 2. Deferred past Phase 5 (in scope later, not now)

These are features we will build, but not in Phases 1–5. Re-evaluated at phase boundaries.

### 2.1 AI avatar presenters (talking heads with lipsync)

**Meaning.** A generated face on screen that speaks as the narrator.

**Why deferred.** The technology is improving but introduces uncanny-valley, identity-rights, and deepfake-adjacency concerns. Through Phase 4 we are narration-over-animation only. Revisited Phase 6 if market signal demands it and the ethics framework is clear.

### 2.2 Real-time / streaming generation

**Meaning.** User types a prompt, starts watching a video while it's being generated, content streams as it renders.

**Why deferred.** Real-time generation requires parallel per-segment delivery, backpressure handling, resumption on failure, and a completely different UX. The fundamental pipeline needs to be reliable at batch first. Candidate for Phase 6.

### 2.3 Native mobile apps (iOS/Android)

**Meaning.** A native Swift or Kotlin app that lets users generate or edit videos.

**Why deferred.** Native app development doubles platform work. Web-responsive UI covers mobile viewing from Phase 4. Candidate for Phase 6 if mobile creation becomes the dominant use.

### 2.4 Bespoke LMS / course hosting

**Meaning.** A product that hosts entire courses with enrollment, grading, progress tracking.

**Why deferred.** The value is in the asset generation; hosting is a commodity others do well. Phase 6 brings LMS *integrations* (SCORM, xAPI, LTI) so videos can be published into existing LMSes. We don't become one.

### 2.5 Marketplace revenue share

**Meaning.** Third-party creators publish domain packs / brand kits / skill packs and earn money when other users buy them.

**Why deferred.** Marketplace economics (discovery, moderation, payouts, tax, fraud) are a business in their own right. Phase 6 introduces the SDK and publishing mechanism — pricing-and-payouts is past the current horizon.

### 2.6 Bring-your-own-model fine-tuning

**Meaning.** Customer uploads their own corpus and we fine-tune a model to match their style / domain.

**Why deferred.** Fine-tuning infrastructure, customer-data handling, model-storage costs — none of this pays off until we have paying enterprise customers with data they can't share publicly. Phase 6+ enterprise conversation.

### 2.7 Handwriting recognition from scanned notes

**Meaning.** Upload handwritten notes, get a video back.

**Why deferred.** Requires OCR, handwriting-to-LaTeX conversion, and a completely different input pipeline. Potentially valuable for educators but not on the critical path.

### 2.8 Interactive video (embedded quizzes, branching)

**Meaning.** Videos that pause for user input and branch based on answers.

**Why deferred.** Interactive video requires a player, not just a file. Phase 5 adds "pause-and-think" beats (cosmetic); Phase 6 could add true interactivity if paired with an LMS integration.

### 2.9 Voice cloning for end users

**Meaning.** Users upload a voice sample and their generated videos narrate in their voice.

**Why deferred to Phase 5.** ElevenLabs' Professional Voice Clone requires uploader-verified consent, which means a consent-capture flow we build once Phases 1–4 prove the product.

### 2.10 Music bed and SFX

**Meaning.** Background music and sound effects in generated videos.

**Why deferred to Phase 5.** Requires licensing (or generative music), mixing rules, ducking during narration. Nice-to-have, not need-to-have; narration over animation is the core product through Phase 4.

---

## 3. Explicitly out of Phase 1 (in scope Phase 2+)

Phase 1 is intentionally narrow. These features are promised for later phases but not Phase 1, and we're noting them here so they're not sneaked in during the tracer-bullet weeks.

- Critic-driven scene regeneration (Phase 2).
- Scene-level regeneration without full pipeline re-run (Phase 2).
- Visual Critic and Factual Verifier agents (Phase 2).
- Multiple voices, voice direction markup (Phase 2).
- Trace UI in the browser (Phase 2).
- Domains beyond calculus (Phase 3).
- Multi-language (Phase 5).
- Web app of any kind (Phase 4).
- REST API / SDK (Phase 4).
- Brand kits (Phase 4).
- User accounts (Phase 4).
- Subtitle rendering in non-English (Phase 5).
- Transitions beyond crossfade (Phase 2).
- 1080p rendering (Phase 4 production; Phase 1 is 720p).
- Music, SFX, audio post beyond level normalization (Phase 5).
- 3D scenes (Phase 5).
- Code execution visualizations (Phase 5).
- Template marketplace (Phase 6).

If in week 3 of Phase 1 we find ourselves adding any of the above, we stop, write it down in `workflows/lessons.md` as a scope-creep incident, and cut it. The kill criteria and phase gates exist precisely to enforce this.

---

## 4. How to reopen a non-goal

A non-goal is not a commandment — it's a decision with a cost. To reopen one:

1. Open a PR editing this file, moving the item out of its current section.
2. Write one paragraph stating what changed that makes it worth reopening (new evidence, new user signal, new technical capability).
3. If the change affects Phase 1–5 scope, update ROADMAP.md in the same PR.
4. If the change affects architecture or risks, update ARCHITECTURE.md / RISKS.md too.
5. Single reviewer approval (Rachit, for now). The point is a paper trail, not a bureaucracy.

No non-goal is overridden by a verbal "let's just add this real quick." The written record is the record.

---

## 5. Confirmation of Artifact 1's non-goals list

Each item Rachit pre-confirmed in Artifact 1, mapped to this document:

| Artifact 1 item | Disposition here |
|---|---|
| 9.1 Generative-video-based content | §1.1 Permanent |
| 9.2 AI avatar presenters through Phase 4 | §2.1 Deferred past Phase 5 |
| 9.3 Real-time / streaming generation | §2.2 Deferred |
| 9.4 Native mobile apps | §2.3 Deferred |
| 9.5 Bespoke LMS / course hosting | §2.4 Deferred / bounded by integrations only |
| 9.6 Content moderation beyond baseline | §1.5 Permanent for Phase 1–3; bounded after |
| 9.7 Marketplace economy | §2.5 Deferred |
| 9.8 Bring-your-own-model fine-tuning | §2.6 Deferred |
| 9.9 Live classroom tools | §1.2 Permanent |
| 9.10 Handwriting recognition as input | §2.7 Deferred |

All 10 confirmed. No unresolved items.
