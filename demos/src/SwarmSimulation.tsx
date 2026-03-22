import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { colors, fonts } from "./theme";

const AGENTS = [
  { name: "Dr. Sarah Chen", role: "AI Researcher", sentiment: "excited", color: "#4f46e5", x: 80, y: 100 },
  { name: "Marcus Rodriguez", role: "VC Partner", sentiment: "cautious", color: "#06d6a0", x: 440, y: 100 },
  { name: "Rep. James Liu", role: "Tech Regulator", sentiment: "concerned", color: "#ef4444", x: 80, y: 280 },
  { name: "Lisa Park", role: "Startup Founder", sentiment: "optimistic", color: "#f59e0b", x: 440, y: 280 },
  { name: "Alex Thompson", role: "Tech Journalist", sentiment: "analytical", color: "#ec4899", x: 80, y: 460 },
  { name: "Yuki Tanaka", role: "ML Engineer", sentiment: "excited", color: "#8b5cf6", x: 440, y: 460 },
];

const POSTS = [
  { agent: 0, text: "GPT-5's reasoning capabilities are a paradigm shift. This changes everything for our research.", time: 0, platform: "twitter" },
  { agent: 1, text: "The enterprise pricing model signals a shift. Watching closely for adoption metrics before committing.", time: 1, platform: "twitter" },
  { agent: 2, text: "We need guardrails before deployment. Submitting proposal for mandatory safety audits on frontier models.", time: 2, platform: "reddit" },
  { agent: 3, text: "Just pivoted our roadmap. If GPT-5 delivers on benchmarks, we're building on top of it.", time: 3, platform: "twitter" },
  { agent: 4, text: "Sources say internal tests show 3x improvement on complex reasoning. Publishing analysis tomorrow.", time: 4, platform: "twitter" },
  { agent: 5, text: "Ran benchmarks overnight. The code generation quality is genuinely impressive. Thread below.", time: 5, platform: "reddit" },
];

export const SwarmSimulation = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  // Round counter
  const roundProgress = interpolate(frame, [0, 8 * fps], [1, 5], { extrapolateRight: "clamp" });
  const currentRound = Math.min(5, Math.floor(roundProgress));

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
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.15em", color: colors.nodeColors[2], marginBottom: 4 }}>
          Step 2
        </div>
        <div style={{ fontSize: 20, fontWeight: 700, color: colors.text }}>
          Swarm Simulation
        </div>
      </div>

      {/* Round indicator */}
      <div
        style={{
          position: "absolute",
          top: 24,
          right: 32,
          opacity: phaseOpacity,
          fontFamily: fonts.headline,
          textAlign: "right",
        }}
      >
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.15em", color: colors.textMuted }}>
          Round
        </div>
        <div style={{ fontSize: 28, fontWeight: 800, color: colors.text }}>
          {currentRound}<span style={{ fontSize: 14, color: colors.textMuted }}>/5</span>
        </div>
      </div>

      {/* Two-column layout: Agents | Feed */}
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
        {/* Agent sidebar */}
        <div style={{ width: 200, display: "flex", flexDirection: "column", gap: 8 }}>
          {AGENTS.map((agent, i) => {
            const delay = Math.round(0.3 * fps + i * 6);
            const s = spring({ frame: frame - delay, fps, config: { damping: 200 } });
            const isActive = POSTS.some(
              (p) => p.agent === i && frame >= Math.round((p.time * 1.2 + 1) * fps) && frame < Math.round((p.time * 1.2 + 2.5) * fps)
            );
            return (
              <div
                key={i}
                style={{
                  opacity: s,
                  background: isActive ? "rgba(79,70,229,0.15)" : colors.bgCard,
                  border: `1px solid ${isActive ? colors.primary : colors.border}`,
                  borderRadius: 10,
                  padding: "10px 12px",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  transition: "none",
                }}
              >
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    background: agent.color,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 12,
                    fontWeight: 700,
                    color: "#fff",
                    fontFamily: fonts.headline,
                    flexShrink: 0,
                  }}
                >
                  {agent.name.split(" ").map((w) => w[0]).join("")}
                </div>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: colors.text, fontFamily: fonts.headline }}>
                    {agent.name.split(" ")[0]}
                  </div>
                  <div style={{ fontSize: 9, color: colors.textMuted }}>{agent.role}</div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Feed */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10, overflow: "hidden" }}>
          {POSTS.map((post, i) => {
            const postStart = Math.round((post.time * 1.2 + 1) * fps);
            return (
              <Sequence key={i} from={postStart} premountFor={fps}>
                <PostCard post={post} agent={AGENTS[post.agent]} index={i} />
              </Sequence>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const PostCard = ({
  post,
  agent,
  index,
}: {
  post: (typeof POSTS)[0];
  agent: (typeof AGENTS)[0];
  index: number;
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 20, stiffness: 180 } });
  const y = interpolate(s, [0, 1], [30, 0]);

  // Typewriter effect
  const charsVisible = Math.round(
    interpolate(frame, [0, 1.5 * fps], [0, post.text.length], { extrapolateRight: "clamp" })
  );
  const displayText = post.text.slice(0, charsVisible);

  return (
    <div
      style={{
        background: colors.bgCard,
        border: `1px solid ${colors.border}`,
        borderRadius: 12,
        padding: "14px 16px",
        opacity: s,
        transform: `translateY(${y}px)`,
        fontFamily: fonts.body,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
        <div
          style={{
            width: 24,
            height: 24,
            borderRadius: "50%",
            background: agent.color,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 9,
            fontWeight: 700,
            color: "#fff",
            fontFamily: fonts.headline,
          }}
        >
          {agent.name.split(" ").map((w) => w[0]).join("")}
        </div>
        <span style={{ fontSize: 11, fontWeight: 700, color: colors.text }}>
          {agent.name}
        </span>
        <span
          style={{
            fontSize: 9,
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            padding: "2px 6px",
            borderRadius: 4,
            background: post.platform === "twitter" ? "rgba(29,155,240,0.15)" : "rgba(255,69,0,0.15)",
            color: post.platform === "twitter" ? "#1d9bf0" : "#ff4500",
          }}
        >
          {post.platform}
        </span>
      </div>
      <div style={{ fontSize: 12, lineHeight: 1.55, color: colors.text }}>
        {displayText}
        {charsVisible < post.text.length && (
          <span style={{ opacity: frame % 15 < 8 ? 1 : 0, color: colors.primaryLight }}>|</span>
        )}
      </div>
    </div>
  );
};
