import { Composition, registerRoot } from "remotion";
import { KnowledgeGraph } from "./KnowledgeGraph";
import { SwarmSimulation } from "./SwarmSimulation";
import { ReportGeneration } from "./ReportGeneration";

const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="KnowledgeGraph"
        component={KnowledgeGraph}
        durationInFrames={240}
        fps={30}
        width={800}
        height={600}
      />
      <Composition
        id="SwarmSimulation"
        component={SwarmSimulation}
        durationInFrames={300}
        fps={30}
        width={800}
        height={600}
      />
      <Composition
        id="ReportGeneration"
        component={ReportGeneration}
        durationInFrames={240}
        fps={30}
        width={800}
        height={600}
      />
    </>
  );
};

registerRoot(RemotionRoot);
