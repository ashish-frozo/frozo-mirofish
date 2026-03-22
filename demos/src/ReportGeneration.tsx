import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { colors, fonts } from "./theme";

const REPORT_SECTIONS = [
  { title: "Executive Summary", icon: "description" },
  { title: "Sentiment Analysis", icon: "analytics" },
  { title: "Key Stakeholder Reactions", icon: "groups" },
  { title: "Risk Assessment", icon: "warning" },
  { title: "Recommendations", icon: "lightbulb" },
];

const FINDINGS = [
  { label: "Developer Sentiment", value: "78%", color: colors.nodeColors[2], desc: "Positive" },
  { label: "Investor Confidence", value: "62%", color: colors.nodeColors[3], desc: "Cautious" },
  { label: "Regulatory Risk", value: "High", color: colors.nodeColors[4], desc: "3 concerns flagged" },
];

const REPORT_LINES = [
  "Based on swarm simulation of 8 autonomous agents across 5 rounds,",
  "the predicted public reaction to the GPT-5 release follows a",
  "bifurcated pattern: technical communities show strong enthusiasm",
  "(78% positive sentiment) while regulatory stakeholders express",
  "heightened concern around safety and governance frameworks.",
  "",
  "Key finding: Developer adoption intent exceeds previous launches",
  "by an estimated 2.3x, driven by reasoning benchmark improvements.",
];

export const ReportGeneration = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const phaseOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: colors.bg }}>
      {/* Header */}
      <div
        style={{
          position: "absolute",
          top: 24,
          left: 32,
          opacity: phaseOpacity,
          fontFamily: fonts.headline,
        }}
      >
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.15em", color: colors.nodeColors[3], marginBottom: 4 }}>
          Step 3
        </div>
        <div style={{ fontSize: 20, fontWeight: 700, color: colors.text }}>
          Prediction Report
        </div>
      </div>

      {/* Main content area */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 32,
          right: 32,
          bottom: 24,
          display: "flex",
          gap: 16,
        }}
      >
        {/* Left: Report outline */}
        <div style={{ width: 200, display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: colors.textMuted, marginBottom: 4, fontFamily: fonts.body }}>
            Report Sections
          </div>
          {REPORT_SECTIONS.map((section, i) => {
            const delay = Math.round(0.5 * fps + i * 12);
            const s = spring({ frame: frame - delay, fps, config: { damping: 200 } });
            const isWriting = frame >= delay && frame < delay + Math.round(2 * fps);
            return (
              <div
                key={i}
                style={{
                  opacity: s,
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 12px",
                  background: isWriting ? "rgba(79,70,229,0.15)" : colors.bgCard,
                  border: `1px solid ${isWriting ? colors.primary : colors.border}`,
                  borderRadius: 10,
                  fontFamily: fonts.body,
                }}
              >
                <div
                  style={{
                    width: 20,
                    height: 20,
                    borderRadius: 6,
                    background: s >= 0.99 && !isWriting ? colors.nodeColors[2] : colors.primary,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 11,
                    color: "#fff",
                    fontWeight: 700,
                  }}
                >
                  {s >= 0.99 && !isWriting ? "✓" : i + 1}
                </div>
                <span style={{ fontSize: 11, fontWeight: 600, color: colors.text }}>
                  {section.title}
                </span>
              </div>
            );
          })}
        </div>

        {/* Right: Report content */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          {/* Report text area */}
          <Sequence from={Math.round(1 * fps)} premountFor={fps}>
            <ReportText />
          </Sequence>

          {/* Stats cards */}
          <Sequence from={Math.round(4.5 * fps)} premountFor={fps}>
            <FindingsCards />
          </Sequence>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const ReportText = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fullText = REPORT_LINES.join("\n");
  const charsVisible = Math.round(
    interpolate(frame, [0, 4 * fps], [0, fullText.length], { extrapolateRight: "clamp" })
  );
  const displayText = fullText.slice(0, charsVisible);

  return (
    <div
      style={{
        background: colors.bgCard,
        border: `1px solid ${colors.border}`,
        borderRadius: 12,
        padding: "20px 24px",
        fontFamily: fonts.body,
        flex: 1,
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 700, color: colors.primaryLight, marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
        Executive Summary
      </div>
      <div style={{ fontSize: 12, lineHeight: 1.7, color: colors.text, whiteSpace: "pre-wrap" }}>
        {displayText}
        {charsVisible < fullText.length && (
          <span style={{ opacity: frame % 15 < 8 ? 1 : 0, color: colors.primaryLight }}>|</span>
        )}
      </div>
    </div>
  );
};

const FindingsCards = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div style={{ display: "flex", gap: 12 }}>
      {FINDINGS.map((finding, i) => {
        const s = spring({
          frame: frame - i * 8,
          fps,
          config: { damping: 15, stiffness: 150 },
        });
        const y = interpolate(s, [0, 1], [20, 0]);
        return (
          <div
            key={i}
            style={{
              flex: 1,
              background: colors.bgCard,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
              padding: "16px 16px",
              opacity: s,
              transform: `translateY(${y}px)`,
              fontFamily: fonts.body,
            }}
          >
            <div style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: colors.textMuted, marginBottom: 8 }}>
              {finding.label}
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, color: finding.color, fontFamily: fonts.headline }}>
              {finding.value}
            </div>
            <div style={{ fontSize: 10, color: colors.textMuted, marginTop: 4 }}>
              {finding.desc}
            </div>
          </div>
        );
      })}
    </div>
  );
};
