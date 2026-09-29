---
name: dendrite-architecture-diagrams
description: Exhaustive master guide for generating professional, high-fidelity Dendrite architecture diagrams (v3.3 Executive Standard).
---

# 🌳 Dendrite Diagramming Skill (Executive Standard v3.3 — One-Shot Master Guide)

Dendrite is a high-fidelity React/SVG visualization framework designed for DSL-driven architectural modeling. This skill document defines the **Google Cloud Executive Reference Standard** for creating dense, balanced, zero-dead-space architecture diagrams in a **single shot** using the Dendrite DSL.

**When asked to generate or refine a Dendrite diagram, you MUST follow this guide as your default paradigm.**

---

## 0. Archetype Decision Router & Canonical 16:9 Bento Matrix System

Every enterprise cloud diagram in Dendrite is a **2D Widescreen Bento Grid (`16:9`)** — **NEVER** a tall Mermaid `flowchart TD` vertical totem pole.

### Quick Archetype Decision Router (Pick the Best Blueprint for the Prompt)

| User Prompt / Architecture Scenario | Canonical Bento Archetype (`layout: matrix`) | Where to Read the Full Template |
| :--- | :--- | :--- |
| **Enterprise Platform / Agentic Governance / 4-Tier Cloud** (Perimeter + Execution + Governance + Data/Tools) | **`BENTO-SANDWICH`** (`5×3` or `2×3`: Top Banner + Middle Split + Bottom Foundation) | **Inline Section 7** below (`gcp-agent-governance.dendrite`) |
| **Option A vs. Option B Comparison / Sync vs. Async / Batch vs. Stream / Custom ADK vs. Managed CXAS** | **`BENTO-DUAL-PATH`** (`3×2`: `"upstream archA archB"` over `"upstream store store"`) | **Inline Section 8** below + [`{skill_dir}/references/dual_path_comparisons.md`](references/dual_path_comparisons.md) |
| **Multi-Region Control Plane (`ew1`/`ew4`/`ew9`) + Global Shared VPC + VPC-SC Perimeter + External SaaS** | **`BENTO-CONTROL-VPC`** (`3×2`: `"region control capacity"` over `"vpc vpc vpc"` + `dockTo`) | [`{skill_dir}/references/multi_region_and_mega_grid.md`](references/multi_region_and_mega_grid.md) (Example C) |
| **Large 8–10 Zone Executive HLD** (Front Door, Control Plane, AI Gateway, Models, Domain Agents, FinOps, Network, Kill Switch, Legend) | **`BENTO-MEGA-GRID`** (`4×3` Matrix + `@ProposalCard` + `@LegendRow` Swatches) | [`{skill_dir}/references/multi_region_and_mega_grid.md`](references/multi_region_and_mega_grid.md) (Example D) |
| **4 Parallel Channels / Domain Agents over Transversal Bus & Data Lakehouse Foundations** (`6–7 Zones`) | **`4-PILLAR-TRANSVERSAL`** (`cols: 4`, `["z1 z2 z3 z4", "z5 z5 z6 z6", "z7 z7 z7 z7"]`) | [`{skill_dir}/references/multi_agent_and_transversals.md`](references/multi_agent_and_transversals.md) (Examples E & F) |
| **Animated Packet Scenarios (`animation`) & Toggleable Multi-Layer Flows (`paths: [...]`)** | **Multi-Stage Animated Mesh** (`step 1..N` packet flows + layer pills) | [`{skill_dir}/references/multi_agent_and_transversals.md`](references/multi_agent_and_transversals.md) (Example G) |
| **12 Geometric Flowchart/System Shapes (`hexagon`, `cylinder`, `queue`, `diamond`, `octagon`, etc.) & 6 Curve Types** | **Shape & Routing Benchmark** (`shape: ...`, `curve: step|bezier|smooth|orthogonal|straight`) | [`{skill_dir}/references/shapes_routing_and_hybrid_net.md`](references/shapes_routing_and_hybrid_net.md) (Example H) |
| **Hybrid / Multi-Cloud Networking (On-Prem + AWS/Azure -> NCC Hub -> Shared VPC Spokes)** | **`NCC-HUB-SPOKE`** (`dockTo: "left"` Hybrid Sources $\rightarrow$ NCC Hub $\rightarrow$ Regional Spokes) | [`{skill_dir}/references/shapes_routing_and_hybrid_net.md`](references/shapes_routing_and_hybrid_net.md) (Example I) |

### The 4 Universal Bento & Matrix Laws
1. **Max-3-Card Vertical Ceiling**: **NO column anywhere in the diagram may exceed 3–4 stacked cards (`<= 420px`).** If a zone has 4–8 cards, use `layout: row`, `layout: matrix` (`cols: 2` or `cols: 4`), or side-by-side `@Ghost` columns (`2+2` or `2+3`).
2. **Side-by-Side Internal Sub-Zones (`layout: row`)**: Whenever an architecture branch (`Arch A` or `Arch B`) has multiple internal sub-stages (`Ingestion` + `Conversational AI`, or `Inline Processing` + `Inline Decision`), the branch container **MUST** use `layout: row` to place those sub-zones **side-by-side**, NEVER stacked vertically (`layout: column`).
3. **Never Stack Upstream on Top of Branches**: Place Upstream/Ingress in the **left column** (`"upstream"`) and shared/wide storage in the **bottom spanning band** (`"upstream store store"`).
4. **Zero-Orphan Matrix Cell Invariant ($\sum (\text{span}_i \times \text{rowSpan}_i) = \text{cols} \times \text{rows}$)**:
   - Every `layout: matrix` container MUST completely tile its `cols × rows` rectangle with **zero empty slots**.
   - Always declare an explicit `areas: [...]` template map on the parent `Zone` and matching `area: "<name>"` on every direct child so the final row is never partially occupied.
   - For **3 Primary Zones**, never use a 2×2 grid with an empty corner; use one of the 6 zero-dead-space 3-zone blueprints:
     - **Bottom Span**: `areas: ["z1 z2", "z3 z3"]`
     - **Top Span**: `areas: ["z1 z1", "z2 z3"]`
     - **Left Tall**: `areas: ["z1 z2", "z1 z3"]`
     - **Right Tall**: `areas: ["z1 z2", "z3 z2"]`
     - **L-Polyomino**: `areas: ["z1 z1 z2", "z3 z2 z2"]` (renders `z2` as a unified 6-sided L-shaped SVG boundary)
     - **3-Col Row**: `cols: 3`, `sizes: ["1.02fr", "1.52fr", "0.66fr"]`

---

## 1. Complete DSL Syntax & Property Reference

### A. Global Header Directives & Constants
```dendrite
theme: "gcp-pro"           // "gcp-pro" | "gcp-architecture" | "gcp-aaa"
renderOrder: nodes-first   // CRITICAL DEFAULT: renders cards before edges so card borders never clip arrowheads
direction: right           // "right" | "down" | "left" | "up"
spacing: 36                // Root canvas gap in pixels

const GcpBlue = "#1a73e8"  // Reusable constant referenced as $GcpBlue
```
- **Built-in Color Functions**: `darken("#f8d3c8", 12)`, `lighten("#1a73e8", 20)`, `alpha("#1a73e8", 0.15)` can be used in any color property.

### B. Reusable Styles (`Style @Name { ... }`)
```dendrite
Style @ProductCard {
  width: 174, height: 58,
  fill: "#ffffff", strokeColor: "#dadce0", strokeWidth: 1, borderRadius: 8,
  fontColor: "#202124", subFontColor: "#5f6368",
  fontSize: 14, subFontSize: 11, labelWeight: bold,
  textAlign: "left", textVAlign: "middle",
  iconPosition: "left", iconSize: 28, padding: 10,
  shadow: true
}
Style @GatewayHubCard {
  base: @ProductCard,      // Inherits all properties from @ProductCard
  width: 204, height: 68, strokeColor: $GcpBlue, strokeWidth: 2
}
```

### C. Containers (`Zone @ID { ... }` or `Zone "ID" { ... }`)
- **Identity & Headers**: `title: "1. Front Door"`, `subtitle: "europe-west9 (Ingress)"`, `headerRight: "Region / Shared VPC"`, `category: "Compute Zone"`, `icon: "GoogleCloud"`, `iconSize: 24`.
- **Layout Engines**:
  - `layout: row` | `layout: column` | `layout: matrix` | `layout: grid` | `layout: manual`
  - `cols: 3`, `sizes: ["1fr", "1.2fr", "1fr"]`, `areas: ["z1 z2", "z3 z3"]`, `area: "z1"`, `span: 2`, `rowSpan: 2`
  - `gap: 20` (or axis-specific `columnGap: 32, rowGap: 24`), `padding: 18`, `align: "center" | "stretch" | "start"`, `justify: "center" | "start"`
- **Visual Styling**: `style: @PerimeterZone`, `fill: "#e8f0fe"`, `strokeColor: "#8ab4f8"`, `strokeWidth: 1.5`, `borderRadius: 12`, `dashed: true`.
- **Relative External Clamping (`dockTo`)**: `dockTo: "TargetZoneID"`, `dockSide: "left" | "right" | "top" | "bottom"`, `dockAlign: "center" | "start" | "end"`, `dockGap: 28`, `dockOffset: 0`.

### D. Leaf Cards (`[id: "Primary Title" | "Optional SubLabel"] { ... }`)
- **Two-Line Title + SubLabel Pipe Syntax**: `[apigee_gw: "Apigee X\nGateway" | "API Management"] { style: @ProductCard, icon: "Apigee" }` (or set `subLabel: "API Management"` inside `{ ... }`).
- **12 Geometric Shapes (`shape`)**:
  `"rectangle"` (default card) | `"pill"` (stadium capsule) | `"hexagon"` (microservice/mesh) | `"cylinder"` (database volume) | `"queue"` (horizontal topic pipe) | `"parallelogram"` (stream I/O) | `"trapezoid"` (load balancer) | `"octagon"` (security gate) | `"subroutine"` (double-walled module) | `"diamond"` (decision router) | `"callout"` (annotation bubble) | `"cloud"` (external cloud boundary).
- **Interactive Badges & Metadata**:
  - `description: "Markdown tooltip shown when clicking the (i) info badge"`
  - `subdiagram: "welcome.dendrite"` or `"#InternalZoneID"` (renders `↗` drilldown badge)
  - `layer: "request"` or `paths: ["01. Ingress Flow"]` (assigns node/edge to interactive filter layers)
  - `iconBg: "#f1f5f9"` (rounded background well behind icon)
  - ` swatch: "arrow" | "dashed-arrow" | "bi-arrow" | "step-arrow" | "dot-arrow" | "card" | "proposal" | "legacy" | "pill" | "telemetry"`, `swatchColor: $GcpBlue`, `swatchWidth: 38`, `tag: "Agreed"`, `tagColor: $GcpBlue`, `tagFill: "#dbeafe"` (for `@LegendRow` cards).

### E. Directed Edges & Orthogonal Routing (`[Source] --> [Target] { ... }`)
- **Valid Arrow Operators ONLY**:
  - `-->` or `->` : Directed solid arrow (`markerEnd: "arrow"`)
  - `<-->` or `<->` : Bidirectional solid arrow (`markerStart: "arrow", markerEnd: "arrow"`)
  - `-.->` : Directed dashed arrow (`dashed: true`)
  - **Trailing Colon Label Shorthand**: `[Source] -> [Target]: "Short Label" { ... }` or `[Source:right] --> [Target:left] { label: "Short Label" }`.
  - **NEVER** use Mermaid/PlantUML operators like `-down->`, `-up->`, `-right->`, or `==>`. Always use `sourceAnchor` / `targetAnchor`!
- **Edge Routing Properties**:
  - `sourceAnchor: "top" | "bottom" | "left" | "right"`, `targetAnchor: "top" | "bottom" | "left" | "right"`
  - `curve: "step"` (default orthogonal elbow router) | `"bezier"` | `"smooth"` | `"orthogonal"` | `"straight"`
  - `color: $GcpBlue`, `strokeWidth: 2`, `dashed: true`, `markerEnd: "arrow" | "diamond" | "circle" | "none"`, `markerSize: 1.0`
  - `label: "MCP / gRPC"`, `labelRatio: 0.65` (`0.0`..`1.0` position along path), `labelStyle: "pill"`
  - `sequenceBadge: "1"`, `badgeFill: $GcpBlue`, `badgeFontColor: "#ffffff"`, `badgeDistance: 0.35`

---

## 2. Executive Typography, Compact Card Geometry & Semantic Palette

Avoid giant bloated cards (`240×100`) and huge container gaps (`80–120px`). Use compact, high-density geometry:

| Element Tier | Style Name | Dimensions (`width × height`) | Font Sizes (`fontSize` / `subFontSize`) | Padding & Gaps |
| :--- | :--- | :--- | :--- | :--- |
| **Root Canvas** | `@ArchitectureRoot` | Auto-fit (`padding: 20–24`) | `22–24px` bold (`iconSize: 28`) | `padding: 22, gap: 18–28` |
| **Primary Zones (`1.`–`4.`)** | `@PerimeterZone`, etc. | Auto-fit or matrix cell | `15–16px` bold (`iconSize: 20`) | `padding: 16–18, gap: 14–20` |
| **Tinted Sub-Zones** | `@PeachSubGroup`, etc. | Auto-fit or matched `width` | `13.5px` bold | `padding: 12, gap: 10–12` |
| **Hero / Gateway Hub** | `@GatewayHubCard` | `204 × 68` (`strokeWidth: 2`) | `15px` bold / `11.5px` subLabel (`iconSize: 30`) | `padding: 12` |
| **Perimeter Actor Card** | `@ActorCard` | `174–186 × 56` (`borderRadius: 8`) | `15px` bold / `11.5px` subLabel (`iconSize: 28`) | `padding: 12` |
| **Standard Service Card** | `@ProductCard` | `164–186 × 56–60` (`borderRadius: 8`) | `14px` bold / `11px` subLabel (`iconSize: 28`) | `padding: 10` |
| **Guardrail / Policy Pill** | `@PolicyPill` | `224–236 × 32` (`borderRadius: 16`) | `13px` bold (`iconSize: 16`) | Inside `gap: 7, padding: 10` |

### Semantic Google Cloud Zone Palette
- **Blue (Perimeter / Ingress / Option A)**: `fill: "#e8f0fe", strokeColor: "#8ab4f8"`
- **Green (Core Governance / Control Plane / Shared Store)**: `fill: "#e6f4ea", strokeColor: "#81c995"`, Sub-zone: `fill: "#ceead6", strokeColor: darken("#ceead6", 14)`
- **Red / Coral (Execution Runtimes / Security Gate / Option B)**: `fill: "#fce8e6", strokeColor: "#f6aea9"`, Sub-zone: `fill: "#f8d3c8", strokeColor: darken("#f8d3c8", 12)`
- **Amber / Yellow (Connected Tools / Data / Shared VPC)**: `fill: "#fef7e0", strokeColor: "#fde293"`, Sub-zone: `fill: "#f9e4a7", strokeColor: darken("#f9e4a7", 14)`
- **Purple (AI / Model Capacity / Agent Mesh)**: `fill: "#f3e8fd", strokeColor: "#c084fc"`
- **Cyan / Teal (Gemini Enterprise / Stream Bus)**: `fill: "#e0f7fa", strokeColor: "#4dd0e1"`

---

## 3. Zero-Dead-Space Layout Math (`TopRowWidth == BottomRowWidth`)

When building a multi-row container (such as a 2-row Governance Zone or a 2-band Enterprise Architecture), **never leave an uneven row that creates a dead corner**. Use `@Ghost` wrappers (`fill: transparent, strokeWidth: 0, fontColor: transparent, padding: 0`) and balance the pixel widths of stacked rows using exact box-model math:

$$\text{RowWidth} = \sum_{i=1}^{N} \text{ChildWidth}_i + (N - 1) \times \text{gap}, \qquad \text{SubZoneWidth} = \text{InnerRowWidth} + 2 \times \text{padding}$$

- **Example (Flush 2-Row Zone Packing: `684px == 684px`)**:
  - **Row 1 (`layout: row, gap: 12`)**: `165 + 168 + 162 + 153 + 3 × 12` = **`684px`**
  - **Row 2 (`layout: row, gap: 28`)**: `204` (`Gateway`) + `252` (`Guardrails SubZone`: `232` pill + `2×10` padding) + `172` (`AuthStack`) + `2 × 28` = **`684px`**

---

## 4. The 7 One-Shot Planar Wiring & Anti-Hallucination Laws (CRITICAL!)

To guarantee a clean, zero-overlap, publication-grade diagram on the very first run, strictly obey these **7 Planar Wiring Laws**:

1. **Zero Orphan Nodes Law**: Every single node or zone ID referenced in an edge `[Source] --> [Target]` **MUST** be declared inside a `Zone` first. Never reference undeclared IDs, and never connect a node to itself (`[A] --> [A]`).
2. **Zero Cross-Bento Multi-Column Jump Law**:
   - In a 3-column Bento grid (`upstream | archA | archB` over `upstream | store | store`), **NEVER** draw a horizontal edge from `upstream` (Column 1) jumping over `archA` (Column 2) to reach `archB` (Column 3) — that slices horizontally across `archA`'s cards!
   - Instead, connect `upstream` only into adjacent `archA` (or into `store`), and let `archA` and `archB` interact with the shared bottom `store` band vertically (`sourceAnchor: "bottom", targetAnchor: "top"`).
3. **Planar Monotonic Bottom-Store Matching (`No X-Crossings`)**:
   - When cards in the upper row drop vertical edges (`sourceAnchor: "bottom", targetAnchor: "top"`) into a horizontal row of shared store cards (`[Store_1 | Store_2 | Store_3 | Store_4]`), order the bottom store cards left-to-right to match the horizontal X order of the upper sources (`Left Branch -> Store_1, Store_2`; `Right Branch -> Store_3, Store_4`). Vertical drop lines must **never** cross each other in an `X` pattern.
4. **Same-Column Sequential Chaining (`No Skip-Edges / No Transitive Triangles`)**:
   - Inside any vertical `layout: column` stack `[C1, C2, C3]`, wire sequentially: `[C1] --> [C2]` and `[C2] --> [C3]` with `sourceAnchor: "bottom", targetAnchor: "top"`.
   - **NEVER** draw a skip-edge `[C1] --> [C3]` jumping over `[C2]`, and **NEVER** draw a transitive triangle bypass (`[A] --> [C]` when `[A] --> [B]` and `[B] --> [C]` already exist).
5. **Unidirectional Edge Budget (`12–20 Edges Max`) & Ultra-Short Labels (`<= 14 chars`)**:
   - Never draw two separate reciprocal edges (`[A] --> [B]` AND `[B] --> [A]`) between the same pair; use a single bidirectional edge `[A] <--> [B]` if needed.
   - Keep edge `label` strings **<= 14 characters** (e.g. `"MCP / gRPC"`, `"JWT / CRM"`, `"Storage API"`) so label pills fit cleanly inside routing corridors (`gap >= 28` or `34` when labeled).
6. **Symmetrical 1-to-N Fork Trunks (`gap: 42`)**:
   - When one card fans out to two stacked sub-containers (`[orchestrator] --> [SubZoneTop]` and `[orchestrator] --> [SubZoneBottom]`), give both target sub-containers the **exact same explicit `width`** (e.g. `width: 326`) inside a `@Ghost` column and set `gap: 42` so the router forms a single shared vertical bus trunk.
7. **Concise 2-Line Zone Headers (`title` <= 20 chars + `subtitle`)**:
   - Never cram a 35-character sentence into `Zone` `title` on narrow columns (`width <= 260px`). Put the primary name in `title: "Region"` and secondary context in `subtitle: "europe-west9 (Ingress)"`.

---

## 5. Built-In Colored GCP SVG Icons (`62+` Keys) & Lucide Icon Catalog

All icons below are **100% base64-inlined** into `dendrite.standalone.js` (zero network fetches required). Always use these exact PascalCase `icon` names:

| Category | Built-In Colored GCP & AI SVG Icon Keys (`icon: "..."`) |
| :--- | :--- |
| **AI, Agents & LLMs** | `VertexAI`, `Gemini`, `GoogleAgents`, `AIPlatform`, `AutoML`, `NaturalLanguage`, `SpeechToText`, `TextToSpeech`, `Translation`, `VisionAI`, `VideoAI`, `RecommendationsAI`, `Dialogflow`, `DialogflowCX`, `Claude`, `OpenAI`, `Meta` |
| **Compute & Runtimes** | `GcpCloudRun` (or `CloudRun`), `GKE`, `GcpCompute` (or `ComputeEngine`), `CloudFunctions`, `AppEngine`, `GcpBox` |
| **API, Gateways & Routing** | `Apigee`, `GcpShuffle` (Agent/API Gateway), `CloudEndpoints`, `CloudLoadBalancing`, `CloudDNS`, `CloudCDN`, `CloudNAT`, `CloudInterconnect`, `CloudVPN`, `Networking`, `VirtualPrivateCloud`, `HybridMulticloud` |
| **Databases & Storage** | `BigQuery`, `AlloyDB`, `CloudSpanner` (or `Spanner`), `CloudSQL`, `GcpDatabase`, `Memorystore`, `Firestore`, `Bigtable`, `GcpStorageBucket` (or `CloudStorage`), `Filestore`, `PersistentDisk` |
| **Streaming, Data & Analytics** | `PubSub`, `Dataflow`, `Dataplex`, `Dataproc`, `Dataform`, `DataFusion`, `DataCatalog`, `Composer` (or `CloudComposer`), `Looker` |
| **Security, Identity & IAM** | `GoogleIdentity`, `GcpLock` (or `IAM` / `CloudIAM`), `SecurityCommandCenter`, `CloudArmor`, `KMS` (or `CloudKMS`), `SecretManager`, `CloudDLP`, `BinaryAuthorization`, `CertificateManager` |
| **DevOps, Observability & Mgmt** | `GcpDeveloperTools`, `ManagementTools`, `CloudBuild`, `CloudDeploy`, `ArtifactRegistry`, `CloudMonitoring`, `CloudLogging`, `CloudTrace`, `CloudScheduler`, `CloudTasks`, `CloudBilling`, `GoogleCloud` |
| **Built-In Lucide Vector Icons** | `User`, `Users`, `Laptop`, `Smartphone`, `Phone`, `Server`, `Database`, `HardDrive`, `Cloud`, `Globe`, `Shield`, `ShieldCheck`, `ShieldAlert`, `Lock`, `Key`, `Cpu`, `Layers`, `Activity`, `Sparkles`, `Bot`, `Code`, `GitMerge`, `FolderGit`, `Search`, `Eye`, `Clock`, `PieChart`, `BarChart3`, `MessageSquare`, `Github` |

---

## 6. Relative Clamping (`dockTo`) for External Perimeters & Legend Bars

When placing external actors (`Users`, `Client`), external SaaS/On-Prem sources (`Salesforce`, `SAP / Kafka`, `Snowflake`), or bottom legend bars outside a primary `@GoogleCloudPlatform` matrix container, **never** wrap the diagram in an outer `@Ghost` row with manual offsets. Declare each external group as a top-level `Zone` with `style: @Ghost` and `dockTo`:

```dendrite
Zone @ExternalUsersGroup {
  style: @Ghost, layout: column, gap: 14, align: center
  dockTo: "Region_Zone", dockSide: "left", dockAlign: "center", dockGap: 28
  [Users: "Users"] { style: @ActorCard, width: 148, height: 50, icon: "User" }
  [Client: "Client"] { style: @ActorCard, width: 148, height: 50, icon: "Laptop" }
}
```

---

## 7. Flagship Blueprint #1: `BENTO-SANDWICH` Enterprise 4-Zone Governance (`gcp-agent-governance.dendrite`)

Use this complete, production-verified 4-Zone Enterprise Agentic Governance & MCP architecture when modeling a **multi-tier cloud platform** (Perimeter + Execution Runtimes + Core Governance/Guardrails + Connected MCP Tools & Data):

```dendrite
renderOrder: nodes-first
direction: down

const GcpBlue = "#1a73e8"
const GcpGreen = "#1e8e3e"
const EmeraldTeal = "#0d9488"
const DarkSlate = "#202124"
const SubText = "#5f6368"
const CardBorder = "#dadce0"
const BusStroke = "#334155"
const SurfaceWhite = "#ffffff"

Style @Ghost {
  fill: transparent, strokeWidth: 0, fontColor: transparent, padding: 0
}
Style @ArchitectureRoot {
  fill: "#f8fafd", strokeColor: "#c2d7f5", strokeWidth: 1.5, borderRadius: 16,
  padding: 24, gap: 18, fontColor: "#3c4043", fontSize: 24, labelWeight: bold,
  icon: "GoogleCloud", iconSize: 28
}
Style @PerimeterZone {
  fill: "#e8f0fe", strokeColor: "#8ab4f8", strokeWidth: 1.5, borderRadius: 12,
  padding: 16, gap: 14, fontColor: $DarkSlate, fontSize: 16, labelWeight: bold
}
Style @ExecutionZone {
  fill: "#fce8e6", strokeColor: "#f6aea9", strokeWidth: 1.5, borderRadius: 12,
  padding: 16, gap: 16, fontColor: $DarkSlate, fontSize: 16, labelWeight: bold
}
Style @GovernanceZone {
  fill: "#e6f4ea", strokeColor: "#81c995", strokeWidth: 1.5, borderRadius: 12,
  padding: 16, gap: 14, fontColor: $DarkSlate, fontSize: 16, labelWeight: bold
}
Style @ResourceZone {
  fill: "#fef7e0", strokeColor: "#fde293", strokeWidth: 1.5, borderRadius: 12,
  padding: 16, gap: 16, fontColor: $DarkSlate, fontSize: 16, labelWeight: bold
}
Style @PeachSubGroup {
  fill: "#f8d3c8", strokeColor: darken("#f8d3c8", 12), strokeWidth: 1, borderRadius: 10,
  padding: 12, gap: 10, fontColor: $DarkSlate, fontSize: 13.5, labelWeight: bold
}
Style @GreenSubGroup {
  fill: "#ceead6", strokeColor: darken("#ceead6", 14), strokeWidth: 1, borderRadius: 10,
  padding: 10, gap: 6, fontColor: $DarkSlate, fontSize: 13.5, labelWeight: bold
}
Style @AmberSubGroup {
  fill: "#f9e4a7", strokeColor: darken("#f9e4a7", 14), strokeWidth: 1, borderRadius: 10,
  padding: 12, gap: 12, fontColor: $DarkSlate, fontSize: 13.5, labelWeight: bold
}
Style @ActorCard {
  width: 178, height: 56,
  fill: $SurfaceWhite, strokeColor: $CardBorder, strokeWidth: 1, borderRadius: 8,
  fontColor: $DarkSlate, subFontColor: $SubText,
  fontSize: 15, subFontSize: 11.5, labelWeight: bold,
  textAlign: "left", textVAlign: "middle",
  iconPosition: "left", iconSize: 28, padding: 12, shadow: true
}
Style @ProductCard {
  width: 164, height: 58,
  fill: $SurfaceWhite, strokeColor: $CardBorder, strokeWidth: 1, borderRadius: 8,
  fontColor: $DarkSlate, subFontColor: $SubText,
  fontSize: 14, subFontSize: 11, labelWeight: bold,
  textAlign: "left", textVAlign: "middle",
  iconPosition: "left", iconSize: 28, padding: 10, shadow: true
}
Style @GatewayHubCard {
  base: @ProductCard,
  width: 204, height: 68, strokeColor: $GcpBlue, strokeWidth: 2,
  fontSize: 15, subFontSize: 11.5, iconSize: 32, padding: 12
}
Style @PolicyPill {
  width: 232, height: 32,
  fill: $SurfaceWhite, strokeColor: "#9aa0a6", strokeWidth: 1, borderRadius: 16,
  fontColor: $DarkSlate, fontSize: 13, labelWeight: bold,
  textAlign: "left", textVAlign: "middle",
  iconPosition: "left", iconSize: 16, padding: 10, shadow: true
}

Zone @GoogleCloudEnterprise {
  title: "Google Cloud Platform"
  style: @ArchitectureRoot
  layout: matrix
  areas: [
    "z1 z1 z1 z1 z1",
    "z3 z3 z2 z2 z2",
    "z4 z4 z4 z4 z4"
  ]
  sizes: ["1.08fr", "1.08fr", "0.95fr", "0.95fr", "0.95fr"]
  gap: 20

  Zone @Zone1_Perimeter {
    area: "z1"
    title: "1. User & Management Perimeter"
    style: @PerimeterZone
    layout: row, gap: 18, align: center, justify: center
    [end_user: "End User"] { style: @ActorCard, icon: "User" }
    [admin_user: "Administrator" | "Google Identity"] { style: @ActorCard, width: 186, icon: "GoogleIdentity" }
    [developer: "Developer"] { style: @ActorCard, icon: "GcpDeveloperTools" }
  }

  Zone @Zone3_Execution {
    area: "z3"
    title: "3. Execution Runtimes & Compute"
    style: @ExecutionZone
    layout: row, gap: 42, align: center, justify: center

    [llm_agent_orchestrator: "LLM Agent\nOrchestrator"] {
      style: @ProductCard, width: 170, height: 58, icon: "VertexAI",
      description: "Vertex AI Agent Builder & ADK Multi-Agent Orchestrator"
    }

    Zone @RuntimePlatformsCol {
      style: @Ghost, layout: column, gap: 12, align: stretch

      Zone @ManagedAgentPlatform {
        title: "Managed & Serverless Agent Platforms"
        style: @PeachSubGroup, width: 326, layout: row, align: center, justify: center
        [gemini_enterprise: "Gemini Enterprise" | "Vertex AI"] {
          style: @ProductCard, width: 206, icon: "VertexAI"
        }
      }

      Zone @ContainerRuntimes {
        title: "Kubernetes & Serverless Runtimes"
        style: @PeachSubGroup, dashed: true, width: 326, padding: 12,
        layout: row, gap: 10, align: center, justify: center
        [gke_cluster: "GKE\nCluster"] { style: @ProductCard, width: 144, icon: "GKE" }
        [cloud_run: "Cloud Run"] { style: @ProductCard, width: 144, icon: "GcpCloudRun" }
      }
    }
  }

  Zone @Zone2_Governance {
    area: "z2"
    title: "2. Core Governance & Central Services"
    style: @GovernanceZone
    layout: column, gap: 14, align: center

    Zone @ControlPlaneCards {
      style: @Ghost, layout: row, gap: 12, align: center, justify: center
      [adk: "Agent Dev\nKit (ADK)" | "Developer Tools"] { style: @ProductCard, width: 165, icon: "GcpDeveloperTools" }
      [gcp_console: "Google Cloud\nConsole" | "Management Tools"] { style: @ProductCard, width: 168, icon: "ManagementTools" }
      [agent_registry_api: "Agent\nRegistry API" | "Cloud Database"] { style: @ProductCard, width: 162, icon: "GcpDatabase" }
      [skill_package: "Skill\nPackage"] { style: @ProductCard, width: 153, icon: "GcpBox" }
    }

    Zone @GatewayAndAuthRow {
      style: @Ghost, layout: row, gap: 28, align: center, justify: center

      [agent_gateway: "Agent Gateway" | "Cloud Shuffle"] {
        style: @GatewayHubCard, icon: "GcpShuffle",
        description: "Centralized Apigee X + Model Armor MCP & A2A Gateway"
      }

      Zone @GatewayGuardrails {
        title: "Gateway Guardrails"
        style: @GreenSubGroup, layout: column, gap: 7, align: center
        [security_policies: "Security Policies"] { style: @PolicyPill, icon: "ShieldCheck" }
        [protocol_mediation: "Protocol Mediation"] { style: @PolicyPill, icon: "GcpShuffle" }
        [content_filtering: "Content Filtering"] { style: @PolicyPill, icon: "SecurityCommandCenter" }
      }

      Zone @AuthStack {
        style: @Ghost, layout: column, gap: 12, align: center
        [agent_identity_auth_manager: "Identity Auth\nManager"] { style: @ProductCard, width: 172, icon: "GcpLock" }
        [auth_providers: "Auth\nProviders"] { style: @ProductCard, width: 172, icon: "Key" }
      }
    }
  }

  Zone @Zone4_Resources {
    area: "z4"
    title: "4. Connected MCP Tools & Data Resources"
    style: @ResourceZone
    layout: matrix, cols: 3, sizes: ["1.02fr", "1.52fr", "0.66fr"], gap: 18, align: center

    Zone @IdentitySubZone {
      title: "Cloud Identity & Workload Credentials"
      style: @AmberSubGroup, layout: row, gap: 12, align: center, justify: center
      [adc: "App Default\nCredentials"] { style: @ProductCard, width: 168, icon: "GoogleIdentity" }
      [gcp_iam: "Google Cloud\nIAM"] { style: @ProductCard, width: 164, icon: "GcpLock" }
    }

    Zone @McpToolsSubZone {
      title: "Connected MCP Tool Servers & External APIs"
      style: @AmberSubGroup, layout: row, gap: 12, align: center, justify: center
      [compute_engine: "Compute\nEngine"] { style: @ProductCard, width: 160, icon: "GcpCompute" }
      [custom_mcp_servers: "Custom MCP\nServers"] { style: @ProductCard, width: 166, icon: "Server" }
      [external_apis: "External APIs\n& Tools"] { style: @ProductCard, width: 164, icon: "Globe" }
    }

    Zone @StorageSubZone {
      title: "Artifact Repository"
      style: @AmberSubGroup, layout: row, align: center, justify: center
      [cloud_storage_bucket: "Cloud Storage\nBucket"] { style: @ProductCard, width: 172, icon: "GcpStorageBucket" }
    }
  }
}

[Zone1_Perimeter] --> [agent_gateway] {
  color: $GcpBlue, strokeWidth: 2, sourceAnchor: "bottom", targetAnchor: "left", curve: "step",
  sequenceBadge: "1", badgeFill: $GcpBlue, badgeFontColor: $SurfaceWhite, badgeDistance: 0.36
}
[llm_agent_orchestrator] --> [ManagedAgentPlatform] { color: $GcpBlue, strokeWidth: 2, sourceAnchor: "right", targetAnchor: "left", curve: "step" }
[llm_agent_orchestrator] --> [ContainerRuntimes] { color: $GcpBlue, strokeWidth: 2, sourceAnchor: "right", targetAnchor: "left", curve: "step" }
[ContainerRuntimes] --> [agent_gateway] {
  color: $GcpBlue, strokeWidth: 2, sourceAnchor: "right", targetAnchor: "left", curve: "step",
  sequenceBadge: "2", badgeFill: $GcpBlue, badgeFontColor: $SurfaceWhite, badgeDistance: 0.44
}
[agent_gateway] --> [security_policies] { color: $GcpBlue, strokeWidth: 2, sourceAnchor: "right", targetAnchor: "left", curve: "step" }
[agent_gateway] --> [protocol_mediation] { color: $GcpBlue, strokeWidth: 2, sourceAnchor: "right", targetAnchor: "left", curve: "step" }
[agent_gateway] --> [content_filtering] { color: $BusStroke, strokeWidth: 2, sourceAnchor: "right", targetAnchor: "left", curve: "step" }
[AuthStack] --> [GatewayGuardrails] { color: $GcpGreen, strokeWidth: 1.8, dashed: true, sourceAnchor: "left", targetAnchor: "right", curve: "step" }
[ContainerRuntimes] --> [IdentitySubZone] {
  color: $BusStroke, strokeWidth: 1.8, sourceAnchor: "bottom", targetAnchor: "top", curve: "step",
  label: "Workload IAM", labelRatio: 0.72, sequenceBadge: "3", badgeFill: $BusStroke, badgeFontColor: $SurfaceWhite, badgeDistance: 0.28
}
[agent_gateway] --> [McpToolsSubZone] {
  color: $EmeraldTeal, strokeWidth: 2, sourceAnchor: "bottom", targetAnchor: "top", curve: "step",
  label: "MCP / gRPC", labelRatio: 0.70, sequenceBadge: "4", badgeFill: $EmeraldTeal, badgeFontColor: $SurfaceWhite, badgeDistance: 0.26
}
[auth_providers] <--> [StorageSubZone] {
  color: $BusStroke, strokeWidth: 1.8, dashed: true, sourceAnchor: "bottom", targetAnchor: "top", curve: "step",
  label: "OIDC & Keys", labelRatio: 0.60
}
```

---

## 8. Flagship Blueprint #2: `BENTO-DUAL-PATH` FinTech Payment & Fraud Mesh (`Sync Inline` vs. `Async Graph`)

Use this complete, production-verified `BENTO-DUAL-PATH` template when comparing **two parallel execution paths (`Option A` vs. `Option B` or `Sync` vs. `Async`)** fed by a shared Upstream Ingress column and persisting to a shared Bottom Ledger/Data Foundation:

```dendrite
theme: "gcp-architecture"
renderOrder: nodes-first
direction: right
spacing: 28

const GcpBlue = "#1a73e8"
const DarkSlate = "#202124"
const SubText = "#5f6368"
const CardBorder = "#dadce0"
const SurfaceWhite = "#ffffff"

Style @ProductCard {
  width: 214, height: 64,
  fill: $SurfaceWhite, strokeColor: $CardBorder, strokeWidth: 1, borderRadius: 8,
  fontColor: $DarkSlate, subFontColor: $SubText,
  fontSize: 13.5, subFontSize: 11, labelWeight: bold,
  textAlign: "left", textVAlign: "middle",
  iconPosition: "left", iconSize: 26, padding: 10, shadow: true
}
Style @ZoneBlue   { fill: "#e8f0fe", stroke: "#5b9bf3", borderRadius: 12 }
Style @ZoneGreen  { fill: "#e6f4ea", stroke: "#68b88e", borderRadius: 12 }
Style @ZonePeach  { fill: "#fce8e6", stroke: "#f28b82", borderRadius: 12 }
Style @ZonePurple { fill: "#f3e8fd", stroke: "#a142f4", borderRadius: 12 }

Zone @GoogleCloudPlatform {
  title: "Google Cloud Platform"
  subtitle: "FinTech Payments & Fraud Mesh (Sync Inline vs. Async Graph)"
  icon: "GoogleCloud", iconSize: 22
  layout: matrix, gap: 28, padding: 28, align: "stretch"
  fill: "#f8fafd", stroke: "#dadce0", cornerRadius: 14
  areas: [
    "upstream  archA  archB",
    "upstream  store  store"
  ]

  Zone @Upstream_Ingress {
    title: "Upstream Ingress"
    subtitle: "ISO-20022 Gateway"
    style: @ZonePeach, area: "upstream"
    layout: column, gap: 24, padding: 20, align: "center", icon: "Apigee", iconSize: 20
    [ISO20022_Gateway: "ISO-20022" | "Payment Gateway"] { style: @ProductCard, icon: "Apigee" }
    [Cloud_Armor_WAF: "Cloud Armor" | "WAF / DDoS"] { style: @ProductCard, icon: "CloudArmor" }
    [Apigee_Router: "Apigee X" | "Payment Router"] { style: @ProductCard, icon: "Apigee" }
  }

  Zone @Option_A_Sync {
    title: "Option A: Sync Inline"
    subtitle: "Sub-50ms p99 Scoring"
    style: @ZoneBlue, area: "archA"
    layout: row, gap: 28, padding: 20, align: "stretch", icon: "GcpCloudRun", iconSize: 20

    Zone @Inline_Processing {
      title: "Inline Processing", layout: column, gap: 18, padding: 16, align: "center",
      fill: "#ffffff", stroke: "#8ab4f8", cornerRadius: 10, icon: "GcpCompute", iconSize: 18
      [Cloud_Run_Validator: "Cloud Run" | "Payment Validator"] { style: @ProductCard, icon: "GcpCloudRun" }
      [Memorystore_Redis: "Memorystore Redis" | "Feature Cache"] { style: @ProductCard, icon: "Memorystore" }
    }
    Zone @Inline_Decision {
      title: "Inline Decision", layout: column, gap: 18, padding: 16, align: "center",
      fill: "#ffffff", stroke: "#8ab4f8", cornerRadius: 10, icon: "VertexAI", iconSize: 18
      [VertexAI_Online_Pred: "Vertex AI" | "Online Prediction"] { style: @ProductCard, icon: "VertexAI" }
      [Inline_Decision_Engine: "Decision Engine" | "Allow / Block"] { style: @ProductCard, icon: "GcpCompute" }
    }
  }

  Zone @Option_B_Async {
    title: "Option B: Async Graph"
    subtitle: "Deep Investigation"
    style: @ZonePurple, area: "archB"
    layout: row, gap: 28, padding: 20, align: "stretch", icon: "VertexAI", iconSize: 20

    Zone @Async_Processing_Detection {
      title: "Streaming Graph ML", layout: column, gap: 18, padding: 16, align: "center",
      fill: "#ffffff", stroke: "#a142f4", cornerRadius: 10, icon: "Dataflow", iconSize: 18
      [Cloud_PubSub_Stream: "Cloud Pub/Sub" | "Payment Stream"] { style: @ProductCard, icon: "PubSub" }
      [Cloud_Dataflow: "Cloud Dataflow" | "Windowed Enrich"] { style: @ProductCard, icon: "Dataflow" }
      [BQML_Graph_Detector: "BigQuery ML" | "Graph Fraud Model"] { style: @ProductCard, icon: "BigQuery" }
    }
    Zone @Agentic_Human_Review {
      title: "Agentic Case Review", layout: column, gap: 18, padding: 16, align: "center",
      fill: "#ffffff", stroke: "#a142f4", cornerRadius: 10, icon: "User", iconSize: 18
      [VertexAI_Case_Inv: "Vertex AI Agent" | "Case Investigator"] { style: @ProductCard, icon: "VertexAI" }
      [Human_Risk_Analyst: "Risk Analyst" | "Case Queue"] { style: @ProductCard, icon: "User" }
    }
  }

  Zone @Shared_Ledger_Security {
    title: "Shared Ledger & Security Foundation"
    subtitle: "ACID Settlement, Audit Trail & HSM Vault"
    style: @ZoneGreen, area: "store"
    layout: row, gap: 24, padding: 20, align: "center", icon: "GcpDatabase", iconSize: 20
    [Cloud_Spanner: "Cloud Spanner" | "Global Ledger"] { style: @ProductCard, icon: "CloudSpanner" }
    [Cloud_KMS_HSM: "Cloud KMS" | "HSM Vault"] { style: @ProductCard, icon: "KMS" }
    [AlloyDB_Audit: "AlloyDB" | "Audit Trail"] { style: @ProductCard, icon: "AlloyDB" }
    [Chronicle_SIEM: "Chronicle SIEM" | "Compliance"] { style: @ProductCard, icon: "SecurityCommandCenter" }
  }
}

[ISO20022_Gateway] -> [Cloud_Armor_WAF] { sourceAnchor: "bottom", targetAnchor: "top", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[Cloud_Armor_WAF] -> [Apigee_Router] { sourceAnchor: "bottom", targetAnchor: "top", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[Apigee_Router] -> [Cloud_Run_Validator] { label: "Sync Path", sourceAnchor: "right", targetAnchor: "left", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[Cloud_Run_Validator] -> [Memorystore_Redis] { label: "Features", sourceAnchor: "bottom", targetAnchor: "top", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[Memorystore_Redis] -> [VertexAI_Online_Pred] { label: "Vector", sourceAnchor: "right", targetAnchor: "left", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[VertexAI_Online_Pred] -> [Inline_Decision_Engine] { label: "Score", sourceAnchor: "bottom", targetAnchor: "top", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[Inline_Decision_Engine] -> [Cloud_Spanner] { label: "Settle Txn", sourceAnchor: "bottom", targetAnchor: "top", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[Cloud_Spanner] <-> [Cloud_KMS_HSM] { label: "CMEK", sourceAnchor: "right", targetAnchor: "left", color: $GcpBlue, strokeWidth: 2, curve: "step" }

[Cloud_PubSub_Stream] -> [Cloud_Dataflow] { label: "Stream", sourceAnchor: "bottom", targetAnchor: "top", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[Cloud_Dataflow] -> [BQML_Graph_Detector] { label: "Enrich", sourceAnchor: "bottom", targetAnchor: "top", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[BQML_Graph_Detector] -> [VertexAI_Case_Inv] { label: "Alert", sourceAnchor: "right", targetAnchor: "left", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[VertexAI_Case_Inv] -> [Human_Risk_Analyst] { label: "Case Brief", sourceAnchor: "bottom", targetAnchor: "top", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[BQML_Graph_Detector] -> [AlloyDB_Audit] { label: "Graph Log", sourceAnchor: "bottom", targetAnchor: "top", color: $GcpBlue, strokeWidth: 2, curve: "step" }
[Human_Risk_Analyst] -> [Chronicle_SIEM] { label: "SAR Filing", sourceAnchor: "bottom", targetAnchor: "top", color: $GcpBlue, strokeWidth: 2, curve: "step" }
```
