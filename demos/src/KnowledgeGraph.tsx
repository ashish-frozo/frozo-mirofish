import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { colors, fonts } from "./theme";

const NODES = [
  { id: 0, label: "GPT-5 Release", x: 400, y: 300, color: colors.primary, size: 44 },
  { id: 1, label: "OpenAI", x: 220, y: 160, color: colors.secondary, size: 34 },
  { id: 2, label: "Developers", x: 580, y: 160, color: colors.nodeColors[2], size: 34 },
  { id: 3, label: "Investors", x: 160, y: 420, color: colors.nodeColors[3], size: 30 },
  { id: 4, label: "Regulators", x: 640, y: 420, color: colors.nodeColors[4], size: 30 },
  { id: 5, label: "Competitors", x: 400, y: 500, color: colors.nodeColors[5], size: 28 },
  { id: 6, label: "Sam Altman", x: 100, y: 280, color: "#8b5cf6", size: 26 },
  { id: 7, label: "EU AI Act", x: 680, y: 280, color: "#f97316", size: 26 },
];

const EDGES: [number, number][] = [
  [0, 1], [0, 2], [0, 3], [0, 4], [0, 5],
  [1, 6], [4, 7], [1, 2], [3, 5], [2, 4],
];

export const KnowledgeGraph = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Phase label
  const phaseOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: colors.bg }}>
      {/* Header */}
      <Sequence from={0} premountFor={fps}>
        <div
          style={{
            position: "absolute",
            top: 24,
            left: 32,
            opacity: phaseOpacity,
            fontFamily: fonts.headline,
          }}
        >
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.15em",
              color: colors.primaryLight,
              marginBottom: 4,
            }}
          >
            Step 1
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: colors.text }}>
            Knowledge Graph
          </div>
        </div>
      </Sequence>

      {/* Document upload animation */}
      <Sequence from={0} durationInFrames={Math.round(2 * fps)} premountFor={fps}>
        <DocumentUpload />
      </Sequence>

      {/* Nodes appear */}
      <svg width={800} height={600} style={{ position: "absolute", top: 0, left: 0 }}>
        {/* Edges */}
        {EDGES.map(([from, to], i) => {
          const edgeDelay = Math.round(2.5 * fps + i * 6);
          const progress = spring({
            frame: frame - edgeDelay,
            fps,
            config: { damping: 200 },
          });
          const n1 = NODES[from];
          const n2 = NODES[to];
          return (
            <line
              key={`e-${i}`}
              x1={n1.x}
              y1={n1.y}
              x2={interpolate(progress, [0, 1], [n1.x, n2.x])}
              y2={interpolate(progress, [0, 1], [n1.y, n2.y])}
              stroke={colors.border}
              strokeWidth={1.5}
              opacity={progress}
            />
          );
        })}

        {/* Nodes */}
        {NODES.map((node, i) => {
          const nodeDelay = Math.round(1.5 * fps + i * 8);
          const s = spring({
            frame: frame - nodeDelay,
            fps,
            config: { damping: 12, stiffness: 120 },
          });
          const scale = interpolate(s, [0, 1], [0, 1]);
          const glow = interpolate(
            frame - nodeDelay,
            [0, 10, 20],
            [0, 0.6, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
          return (
            <g key={node.id} transform={`translate(${node.x}, ${node.y}) scale(${scale})`}>
              {/* Glow */}
              <circle r={node.size + 8} fill={node.color} opacity={glow * 0.4} />
              {/* Node */}
              <circle r={node.size / 2} fill={node.color} opacity={0.9} />
              {/* Label */}
              <text
                y={node.size / 2 + 16}
                textAnchor="middle"
                fill={colors.text}
                fontSize={11}
                fontFamily={fonts.body}
                fontWeight={600}
                opacity={scale}
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Stats counter */}
      <Sequence from={Math.round(5 * fps)} premountFor={fps}>
        <StatsCounter />
      </Sequence>
    </AbsoluteFill>
  );
};

const DocumentUpload = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const slide = spring({ frame, fps, config: { damping: 200 } });
  const y = interpolate(slide, [0, 1], [40, 0]);
  const opacity = interpolate(slide, [0, 1], [0, 1]);
  const fadeOut = interpolate(frame, [1.2 * fps, 1.8 * fps], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 220,
        left: 280,
        width: 240,
        background: colors.bgCard,
        borderRadius: 12,
        padding: "16px 20px",
        border: `1px solid ${colors.border}`,
        transform: `translateY(${y}px)`,
        opacity: opacity * fadeOut,
        fontFamily: fonts.body,
      }}
    >
      <div style={{ fontSize: 10, color: colors.textMuted, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 700 }}>
        Uploading Documents
      </div>
      <div style={{ fontSize: 13, color: colors.text, fontWeight: 600 }}>policy_draft.pdf</div>
      <div style={{ fontSize: 13, color: colors.text, fontWeight: 600, marginTop: 4 }}>market_analysis.md</div>
      <div
        style={{
          marginTop: 12,
          height: 4,
          background: "rgba(79,70,229,0.2)",
          borderRadius: 4,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${interpolate(frame, [0, 1.2 * fps], [0, 100], { extrapolateRight: "clamp" })}%`,
            background: colors.primary,
            borderRadius: 4,
          }}
        />
      </div>
    </div>
  );
};

const StatsCounter = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 200 } });
  const nodes = Math.round(interpolate(s, [0, 1], [0, 8]));
  const edges = Math.round(interpolate(s, [0, 1], [0, 10]));

  return (
    <div
      style={{
        position: "absolute",
        bottom: 24,
        right: 32,
        display: "flex",
        gap: 20,
        opacity: s,
        fontFamily: fonts.body,
      }}
    >
      <div style={{ textAlign: "right" }}>
        <div style={{ fontSize: 24, fontWeight: 700, color: colors.primaryLight, fontFamily: fonts.headline }}>
          {nodes}
        </div>
        <div style={{ fontSize: 10, color: colors.textMuted, textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 600 }}>
          Entities
        </div>
      </div>
      <div style={{ textAlign: "right" }}>
        <div style={{ fontSize: 24, fontWeight: 700, color: colors.accent, fontFamily: fonts.headline }}>
          {edges}
        </div>
        <div style={{ fontSize: 10, color: colors.textMuted, textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 600 }}>
          Relationships
        </div>
      </div>
    </div>
  );
};
