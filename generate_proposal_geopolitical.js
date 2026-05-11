const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, ExternalHyperlink, HeadingLevel,
  BorderStyle, WidthType, ShadingType
} = require('docx');
const fs = require('fs');

const bullets = {
  config: [{
    reference: "bullets",
    levels: [{
      level: 0, format: LevelFormat.BULLET, text: "•",
      alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } }
    }]
  }]
};

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 480, after: 200 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 120 } });
}
function p(runs) {
  const children = typeof runs === 'string'
    ? [new TextRun({ text: runs, size: 24 })]
    : runs;
  return new Paragraph({ children, spacing: { before: 100, after: 100 }, alignment: AlignmentType.JUSTIFIED });
}
function bullet(text) {
  return new Paragraph({
    children: [new TextRun({ text, size: 24 })],
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 60, after: 60 }
  });
}
function run(text, opts = {}) {
  return new TextRun({ text, size: 24, ...opts });
}
function link(text, url) {
  return new ExternalHyperlink({ link: url, children: [new TextRun({ text, style: "Hyperlink", size: 22 })] });
}
function bibEntry(authors, year, title, journal, url) {
  return new Paragraph({
    children: [
      new TextRun({ text: `${authors} (${year}). ${title}. `, size: 22 }),
      new TextRun({ text: journal + '. ', size: 22, italics: true }),
      new ExternalHyperlink({ link: url, children: [new TextRun({ text: "View on Consensus", style: "Hyperlink", size: 22 })] })
    ],
    spacing: { before: 60, after: 60 },
    indent: { left: 360, hanging: 360 }
  });
}
function tableRow(cells, isHeader) {
  return new TableRow({
    children: cells.map((c, i) => new TableCell({
      children: [new Paragraph({
        children: [new TextRun({ text: c, bold: isHeader, size: 20 })],
        spacing: { before: 60, after: 60 }
      })],
      shading: isHeader ? { type: ShadingType.CLEAR, fill: "1F4E79", color: "FFFFFF" } : undefined,
      width: i === 0 ? { size: 18, type: WidthType.PERCENTAGE }
           : i === 1 ? { size: 50, type: WidthType.PERCENTAGE }
           : { size: 32, type: WidthType.PERCENTAGE }
    }))
  });
}

const doc = new Document({
  numbering: bullets,
  styles: { default: { document: { run: { font: "Calibri", size: 24 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1418, right: 1418, bottom: 1418, left: 1418 }
      }
    },
    children: [

      // TITLE BLOCK
      new Paragraph({
        children: [new TextRun({ text: "Doctoral Research Proposal", bold: true, size: 28, color: "1F4E79" })],
        alignment: AlignmentType.CENTER, spacing: { before: 0, after: 80 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "Geopolitical Impunity and Extractive Activity:", bold: true, size: 34 })],
        alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "A Hybrid Physics–ML Framework for Detecting Mining Anomalies in Disputed Territories", bold: true, size: 28 })],
        alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "PhD Proposal — Internal Submission Draft", size: 22, italics: true, color: "666666" })],
        alignment: AlignmentType.CENTER, spacing: { before: 0, after: 600 }
      }),

      // CHAPTER 1
      h1("1. Background and Motivation"),
      p([
        run("The intersection of territorial sovereignty and natural resource extraction has long been recognised as a driver of conflict. When state authority is contested or absent — as in border disputes, de facto partition zones, and post-conflict power vacuums — the governance mechanisms that normally constrain extractive activity collapse. Conflict tends to depopulate territories: residents flee, enforcement personnel withdraw, and the legal apparatus of permitting, monitoring, and prosecution ceases to function. What remains is a resource-rich landscape with minimal resistance to entry. "),
        run("Lambin and Meyfroidt (2011)", { bold: true }),
        run(" established, in a landmark PNAS paper (2,880 citations), that governance pressure in one region systematically displaces extraction to lower-governance zones — a displacement mechanism that operates across deforestation, mining, and land conversion globally. Disputed territories sit at the extreme end of this governance gradient: they are precisely the zones to which extraction migrates when enforcement is weakest.")
      ]),
      p([
        run("The extractive industries literature confirms this dynamic. "),
        run("Bebbington et al. (2011)", { bold: true }),
        run(", analysing Andean-Amazonian territories, documented the convergence of nominally different governance regimes toward aggressive extractive expansion — driven by resource curse dynamics, fiscal pressure, and the absence of effective local contestation. "),
        run("Prem et al. (2020)", { bold: true }),
        run(", using satellite deforestation data and a difference-in-differences identification strategy, showed that the end of Colombia's FARC conflict caused measurable deforestation surges in formerly controlled areas where state capacity was weak — a natural experiment in governance-collapse-driven extraction. These studies establish the empirical regularity: governance vacuums predict extraction, and conflict creates governance vacuums. What they do not provide is a systematic, scalable detection framework that operates in real time across multiple territories.")
      ]),
      p([
        run("Remote sensing has transformed the monitoring of land disturbance. "),
        run("Gallwey et al. (2020)", { bold: true }),
        run(", applying a convolutional neural network to Sentinel-2 multispectral imagery in Ghana, achieved detection of artisanal small-scale mining (ASM) with less than 8% omission/commission error across six million hectares — and demonstrated a measurable response to a 2017 governance intervention. "),
        run("Balaniuk et al. (2020)", { bold: true }),
        run(" identified 263 unregistered mines in Brazil using the same satellite platform and deep learning pipeline. Both studies confirm that extraction invisible to legal enforcement is visible from space. The critical gap in this literature is twofold: first, existing detection methods treat mining as a classification problem rather than as an anomaly relative to a physics-calibrated environmental baseline; second, none of these studies include geopolitical context — dispute status, governance quality, conflict intensity — as predictive covariates.")
      ]),
      p([
        run("Physics-guided machine learning (PGML) has matured into a validated paradigm for environmental monitoring. "),
        run("Willard et al. (2020)", { bold: true }),
        run(", in the canonical ACM Computing Surveys review (490 citations), taxonomised the full design space of approaches for integrating physical models with ML — including residual/delta learning, the architecture most relevant to this research. "),
        run("Shen et al. (2023)", { bold: true }),
        run(", in a Nature Reviews perspective, demonstrated that differentiable modelling — connecting process-based physics to neural networks — produces better generalisability than pure ML under data-scarce conditions. This matters critically for disputed basins, where upstream gauge data may be inaccessible, falsified, or withheld as part of the geopolitical contest itself. "),
        run("Lu et al. (2021)", { bold: true }),
        run(" validated a physics-informed Bayesian LSTM for streamflow prediction in data-scarce basins, demonstrating Nash-Sutcliffe efficiency above 0.8 with only two years of calibration data — the realistic data availability in many contested zones.")
      ]),
      p([
        run("This research addresses the convergence of these three literatures. The core observation is that conflict-driven depopulation creates a distinctive environmental signature: it suppresses anthropogenic background turbidity (agriculture, construction, settlements) while leaving the territory accessible to extractive actors operating outside any governance framework. This produces a favourable signal-to-noise environment for a physics-ML anomaly detection framework: the physical baseline expects low turbidity because land use is suppressed; any observed excess is therefore attributable to active disturbance, most plausibly extraction. The research proposes to operationalise this logic through a six-step pipeline — physical baseline modelling, satellite observation, residual computation, machine learning prediction, causal validation, and game-theoretic mechanism modelling — applied to disputed territories where this detection problem has never been systematically studied.")
      ]),

      // CHAPTER 2
      h1("2. Research Questions"),
      p("This research is structured around one primary question and three sub-questions derived from the identified gaps in the literature:"),
      new Paragraph({ spacing: { before: 160, after: 80 } }),
      p([run("Primary Research Question:", { bold: true })]),
      p([run("RQ0: ", { bold: true }), run("Do geopolitical impunity conditions — operationalised as proximity to sovereignty disputes, governance deficits, and conflict intensity — predict anomalous turbidity residuals (satellite-observed minus physics-predicted suspended sediment concentration) in contested river basins, and does dispute escalation causally increase these residuals above what environmental covariates alone can explain?")]),
      new Paragraph({ spacing: { before: 120, after: 60 } }),
      p([run("Sub-Questions:", { bold: true })]),
      p([run("RQ1: ", { bold: true }), run("Can a physics-ML hybrid framework — SWAT sediment baseline combined with XGBoost/spatiotemporal LSTM residual predictor — reliably detect extraction-driven turbidity anomalies in data-scarce disputed basins while controlling for natural hydrological variability?")]),
      p([run("RQ2: ", { bold: true }), run("Do geopolitical covariates (dispute status from MID/ICOW, governance quality indices, conflict event counts from ACLED) provide statistically significant incremental predictive power for turbidity residuals beyond environmental predictors — precipitation, slope, land cover, seasonality — alone?")]),
      p([run("RQ3: ", { bold: true }), run("Does a multi-agent game-theoretic model, calibrated from the observed residual–escalation relationship, reproduce the timing and magnitude of extraction anomalies across historical dispute cycles — thereby providing a mechanism model that can, once validated, support forward-looking extraction risk scenarios?")]),

      // CHAPTER 3
      h1("3. Positioning in the Literature"),
      p([
        run("Three distinct research communities have developed the tools this proposal integrates, but they have not communicated. The "),
        run("remote sensing and mining detection", { bold: true }),
        run(" community (Gallwey et al. 2020; Balaniuk et al. 2020; Usmanov et al. 2021; McKenna et al. 2020) has produced validated pipelines for satellite-based detection of surface extraction. These studies treat mining as a land-classification or change-detection problem; they do not attempt to explain why extraction occurs where it does, and none include geopolitical variables.")
      ]),
      p([
        run("The "),
        run("physics-guided ML for hydrology", { bold: true }),
        run(" community (Willard et al. 2020; Shen et al. 2023; Lu et al. 2021; Wang et al. 2024; Shuai et al. 2024) has established robust architectures for correcting physics-model residuals with ML. Shuai et al. (2024) demonstrated this exact approach — using XGBoost and LSTM to correct MODFLOW groundwater model residuals — with the critical finding that auxiliary covariates improve performance. However, all existing residual-predictor studies use exclusively environmental covariates. No study has introduced governance quality, dispute status, or conflict event data into a physics-ML residual model.")
      ]),
      p([
        run("The "),
        run("political economy of extraction", { bold: true }),
        run(" community (Lambin & Meyfroidt 2011; Bebbington et al. 2011; Prem et al. 2020; Furlong & Gleditsch 2006) has established causal links between governance conditions and extraction intensity. Prem et al. (2020) represent the frontier: DiD with satellite data, causal identification of governance-driven extraction. But this literature does not use physics-calibrated baselines — it uses raw satellite change detection — and does not attempt mechanism modelling through game theory.")
      ]),
      p([
        run("The "),
        run("game-theoretic modelling of resource conflict", { bold: true }),
        run(" exists in international relations (Bueno de Mesquita et al. 1985) and water allocation (Khorshidi et al. 2024; Vithya et al. 2025). Every such model requires a payoff matrix — a table specifying how much each actor gains or loses under each combination of strategies (enter/wait, extract aggressively/cautiously). The standard practice is to fill this matrix with assumed numbers: the researcher posits that the gain from monopoly extraction is, say, 1.0 and the cost of conflict is 0.5, then solves for equilibrium. The numbers are plausible but untethered from observed behaviour. This research replaces assumption with measurement. When a conflict escalation event is recorded in ACLED and enforcement withdraws from a disputed basin, mining actors respond: the satellite turbidity residual spikes above the physics-predicted baseline within days. The magnitude of that spike, how quickly it appears, how it scales with the number of competing actors, and how fast it collapses when enforcement returns — these observables directly encode the payoff parameters the game requires. For the first time, the payoff matrix is derived from a physical signal in the world rather than from a modeller's prior. This is the hardest gap to bridge, because it demands that Steps 1–5 each work reliably before Step 6 is even attempted — and it is the most significant theoretical contribution of this research.")
      ]),
      p([
        run("This research is the first to: (1) use a physics-calibrated residual — rather than raw satellite change — as the detection signal for extraction; (2) add geopolitical covariates to a physics-ML residual predictor; (3) apply causal identification via staggered DiD to dispute escalation as a treatment affecting a continuous physics-corrected outcome; and (4) calibrate a multi-agent game-theoretic model from observed residual–escalation patterns rather than assumed payoffs.")
      ]),

      // CHAPTER 4
      h1("4. Methodology"),
      h2("4.1 Research Design"),
      p("The study employs a mixed computational-empirical design structured as a six-step pipeline. Steps 1–3 produce the detection signal; Steps 4–5 test its explanatory and causal structure; Step 6 models the underlying strategic mechanism. The pipeline is designed to be applied across multiple case territories — specifically river basins in or adjacent to sovereignty-disputed zones — using publicly available satellite data, open hydrological model infrastructure, and conflict event databases."),

      h2("4.2 Data Sources"),
      bullet("Sentinel-2 MSI imagery (ESA, 10m resolution, 5-day revisit): NDTI time-series via Google Earth Engine for turbidity observation (Step 2)"),
      bullet("SWAT model inputs: SRTM DEM, FAO soil data, Copernicus land cover, ERA5 climate reanalysis. No in-situ gauge dependency for baseline construction (Step 1)"),
      bullet("Geopolitical covariates: MID (Militarized Interstate Dispute) database, ICOW territorial claims dataset, ACLED conflict event database (geocoded, daily resolution), World Governance Indicators (Step 4)"),
      bullet("Conflict event treatment dates: ACLED escalation events as treatment shocks for the event study (Step 5)"),
      bullet("Geological control: pre-dispute mineral prospectivity maps (British Geological Survey World Mineral Statistics; USGS mineral assessments) for endogeneity instrument (Step 4)"),

      h2("4.3 Analytical Pipeline"),
      p([run("Step 1 — Physical Baseline (SWAT):", { bold: true }), run(" Deploy SWAT with ML-based parameter regionalization (following Bawa et al. 2025) to generate expected daily suspended sediment concentration at monitoring points in each target basin. Where calibration data is absent, apply physics-informed Bayesian LSTM fallback (Lu et al. 2021). The model establishes what turbidity would be observed under natural hydrology with no extraction.")]),
      p([run("Step 2 — Satellite Observation (Sentinel-2 NDTI):", { bold: true }), run(" Compute NDTI time-series for each basin using Google Earth Engine. Apply cloud-masking and temporal compositing. Output: observed turbidity signal at 10m / 5-day resolution, co-registered to SWAT monitoring points.")]),
      p([run("Step 3 — Residual Computation:", { bold: true }), run(" Compute the signed residual: observed NDTI minus SWAT-predicted turbidity, normalised by seasonal baseline variance. Positive residuals indicate anomalous suspended sediment above the physics-expected level. This is the primary detection signal.")]),
      p([run("Step 4 — ML Residual Predictor:", { bold: true }), run(" Train XGBoost and spatiotemporal LSTM models to predict the residual from two covariate sets: (a) environmental only (precipitation anomaly, slope, land cover change, flood indicator); (b) environmental + geopolitical (dispute status, MID escalation events, ACLED conflict count, governance index, geological prospectivity). Compare model performance to isolate the marginal contribution of geopolitical covariates (RQ2). Apply SHAP values to decompose feature importance.")]),
      p([run("Step 5 — Causal Validation (Staggered DiD):", { bold: true }), run(" Treat dispute escalation events (from ACLED/MID) as staggered treatment shocks. Apply the Marcus et al. (2020) parallel trends framework to estimate the causal effect of escalation on turbidity residuals, using pre-escalation trends as the control condition and non-disputed adjacent basins as the comparison group. This addresses RQ0 and RQ2.")]),
      p([run("Step 6 — Game-Theoretic Mechanism Model:", { bold: true }), run(" Specify a multi-actor game in which extraction actors choose entry timing and intensity given a payoff structure calibrated from the observed residual–escalation relationship (Steps 3–5). Actors are parameterised by dispute type (international vs. intra-state), enforcement capacity proxy (governance index), and resource prospectivity. Solve for Nash equilibria and assess whether equilibrium extraction timing and magnitude replicate historical residual patterns (RQ3). The validated model provides the mechanism underlying the detected anomalies.")]),

      h2("4.4 Case Selection"),
      p("Target basins will be selected to maximise variation in dispute type, governance regime, and geological prospectivity, while satisfying Sentinel-2 observability (cloud cover < 40% of months). Candidate regions include disputed border zones in the Amazon basin, the Sahel corridor, and Southeast Asia. Final selection is subject to data availability audit in Year 1."),

      // CHAPTER 5
      h1("5. Expected Contributions"),
      h2("5.1 Theoretical Contribution"),
      p([
        run("This research introduces "),
        run("physics-calibrated residual anomaly detection", { bold: true }),
        run(" as a new paradigm for satellite-based extraction monitoring. Existing detection approaches classify land cover or measure change from an arbitrary baseline; this framework uses a calibrated physical model as the counterfactual, producing anomalies that are interpretable in physical units and robust to environmental confounds. This is a methodological contribution to the remote sensing community.")
      ]),
      p([
        run("The integration of "),
        run("geopolitical covariates into physics-ML residual prediction", { bold: true }),
        run(" — to our knowledge the first such application — establishes that governance and conflict variables contain information not captured by environmental predictors. If confirmed, this reframes the ML covariate design question for environmental monitoring: political variables belong alongside physical ones.")
      ]),
      p([
        run("The "),
        run("empirically-calibrated game-theoretic mechanism model", { bold: true }),
        run(" (Step 6) represents the first application of satellite-derived physical signals as inputs to strategic behaviour modelling. This bridges the remote sensing and IR/political economy literatures in a way that neither has previously attempted, and opens a research programme for forward-looking extraction risk scenarios once the retrospective mechanism is validated.")
      ]),

      h2("5.2 Practical Contribution"),
      p("The pipeline produces a replicable, open-source monitoring system applicable to any basin with Sentinel-2 coverage and a matched conflict event database. Outputs — anomaly maps, residual time-series, SHAP attribution — are directly interpretable by environmental enforcement agencies, investigative journalists covering conflict-zone resource extraction, and international bodies (UN Environment Programme, INTERPOL environmental crime units) that monitor illegal mining."),

      h2("5.3 Policy Contribution"),
      p("The causal identification of dispute escalation as a driver of extraction anomalies provides an evidence base for anticipatory governance interventions: deploying monitoring resources and diplomatic pressure before extraction becomes entrenched. The game-theoretic mechanism model, once validated, can generate probabilistic extraction risk maps conditioned on conflict scenario inputs — a direct input to early-warning systems for environmental crime in contested territories."),

      // CHAPTER 6
      h1("6. Research Timeline"),
      new Table({
        width: { size: 100, type: WidthType.PERCENTAGE },
        rows: [
          tableRow(["Period", "Primary Activity", "Key Deliverable"], true),
          tableRow(["Year 1 — S1", "Case selection & data audit; SWAT setup for 2–3 pilot basins; Sentinel-2 GEE pipeline", "Pilot basin selection report; SWAT baseline running for pilot sites"]),
          tableRow(["Year 1 — S2", "NDTI time-series computation; residual computation (Steps 2–3); preliminary anomaly maps", "Residual dataset for pilot basins; Chapter 1 draft submitted"]),
          tableRow(["Year 2 — S1", "ML residual predictor (Step 4): XGBoost + LSTM training; geopolitical covariate integration; SHAP analysis", "ML model results; conference paper on Steps 1–4"]),
          tableRow(["Year 2 — S2", "Causal validation (Step 5): staggered DiD design; parallel trends tests; full basin expansion", "Chapter 2 (Methods + Results Steps 1–5) draft submitted"]),
          tableRow(["Year 3 — S1", "Game-theoretic model specification and calibration (Step 6); equilibrium analysis; back-testing", "Journal article submission (Steps 1–5); Chapter 3 (Game theory) draft"]),
          tableRow(["Year 3 — S2", "Thesis integration; revisions; policy brief; open-source repository release", "Thesis submission; open-source pipeline published"])
        ]
      }),

      // CHAPTER 7
      h1("7. Bibliography"),
      p("All references below were returned by Consensus during the literature review session (May 2026). URLs link directly to the Consensus paper page."),
      new Paragraph({ spacing: { before: 160 } }),

      bibEntry("Balaniuk, R. et al.", "2020", "Mining and Tailings Dam Detection in Satellite Imagery Using Deep Learning", "Sensors", "https://consensus.app/papers/details/4f61b0018db159b0b7dcbd924712a018/?utm_source=claude_code"),
      bibEntry("Bawa, A. et al.", "2025", "Enhancing hydrological modeling of ungauged watersheds through machine learning and physical similarity-based regionalization", "Environmental Modelling & Software", "https://consensus.app/papers/details/be29f0c59d0b5649a8fdbb8315521b97/?utm_source=claude_code"),
      bibEntry("Bebbington, A. et al.", "2011", "An Andean Avatar: Post-Neoliberal and Neoliberal Strategies for Securing the Unobtainable", "New Political Economy", "https://consensus.app/papers/details/75ec7fcb43c25ec0bbf0523458212779/?utm_source=claude_code"),
      bibEntry("Bueno de Mesquita, B. et al.", "1985", "Forecasting Political Events: The Future of Hong Kong", "Yale University Press", "https://consensus.app/papers/details/c9d678c0db1052ce820b886cf6c17819/?utm_source=claude_code"),
      bibEntry("Furlong, K. & Gleditsch, N.P. et al.", "2006", "Geographic Opportunity and Neomalthusian Willingness: Boundaries, Shared Rivers, and Conflict", "International Interactions", "https://consensus.app/papers/details/67c6fc8770525c11baabdd41cacc2383/?utm_source=claude_code"),
      bibEntry("Gallwey, J. et al.", "2020", "A Sentinel-2 based multispectral convolutional neural network for detecting artisanal small-scale mining in Ghana", "Remote Sensing of Environment", "https://consensus.app/papers/details/6fda6793d62e56a3987335d6b8ad752a/?utm_source=claude_code"),
      bibEntry("Godar, J. et al.", "2014", "Actor-specific contributions to the deforestation slowdown in the Brazilian Amazon", "PNAS", "https://consensus.app/papers/details/152b68c80f825ec9b3a40dad3968e94d/?utm_source=claude_code"),
      bibEntry("Khorshidi, M.S. et al.", "2024", "Integrating Agent-Based Modeling and Game Theory for Optimal Water Resource Allocation within Complex Hierarchical Systems", "Journal of Cleaner Production", "https://consensus.app/papers/details/d944dd5ce3ab5b2a984b4a11d4adcd67/?utm_source=claude_code"),
      bibEntry("Lambin, E. & Meyfroidt, P. et al.", "2011", "Global land use change, economic globalization, and the looming land scarcity", "PNAS", "https://consensus.app/papers/details/57f9d89a6be45b95b67b7bf8e43299cc/?utm_source=claude_code"),
      bibEntry("Lu, D. et al.", "2021", "Streamflow simulation in data-scarce basins using Bayesian and physics-informed machine learning models", "Journal of Hydrometeorology", "https://consensus.app/papers/details/b5e9946283165374bb9e3b19f65cc8f6/?utm_source=claude_code"),
      bibEntry("Marcus, M. et al.", "2020", "The Role of Parallel Trends in Event Study Settings: An Application to Environmental Economics", "Journal of the Association of Environmental and Resource Economists", "https://consensus.app/papers/details/e6da3e18eecf5d9c98c76bd129983c2a/?utm_source=claude_code"),
      bibEntry("McKenna, P. et al.", "2020", "Remote Sensing of Mine Site Rehabilitation for Ecological Outcomes: A Global Systematic Review", "Remote Sensing", "https://consensus.app/papers/details/954122d633fb577caff32db08fb1efcc/?utm_source=claude_code"),
      bibEntry("Meyfroidt, P.", "2017", "Trade-offs between environment and livelihoods: Bridging the global land use and food security discussions", "AARN: Politics & Land Use", "https://consensus.app/papers/details/ddaa703846a65edabfde8ae0c1599f3e/?utm_source=claude_code"),
      bibEntry("Prem, M. et al.", "2020", "End-of-conflict deforestation: Evidence from Colombia's peace agreement", "World Development", "https://consensus.app/papers/details/e8cefa4bf39150549f0e3fe2b101d076/?utm_source=claude_code"),
      bibEntry("Qi, J. et al.", "2020", "SWAT ungauged: Water quality modeling in the Upper Mississippi River Basin", "Journal of Hydrology", "https://consensus.app/papers/details/2756fe3ff0105abfa61fe7ef54d6d132/?utm_source=claude_code"),
      bibEntry("Sankaran, R. et al.", "2023", "Retrieval of suspended sediment concentration in the Arabian Gulf water of arid region by Sentinel-2 data", "Science of the Total Environment", "https://consensus.app/papers/details/86d9de7ab9f25ae5b486da6a330cded3/?utm_source=claude_code"),
      bibEntry("Shen, C. et al.", "2023", "Differentiable modelling to unify machine learning and physical models for geosciences", "Nature Reviews Earth & Environment", "https://consensus.app/papers/details/47e78cfecf5257a58908d7d599aa56a0/?utm_source=claude_code"),
      bibEntry("Shuai, G. et al.", "2024", "Comparison of Multiple Machine Learning Methods for Correcting Groundwater Levels Predicted by Physics-Based Models", "Sustainability", "https://consensus.app/papers/details/ad8ddc25de0d5ef2b6c6c67d3e95da5f/?utm_source=claude_code"),
      bibEntry("Usmanov, B. et al.", "2021", "Automated detection of illegal nonmetallic minerals mining places according to Sentinel-2 data", "Unknown Journal", "https://consensus.app/papers/details/2780c013684454fba5f61c2a38348186/?utm_source=claude_code"),
      bibEntry("Vithya, N. et al.", "2025", "Dominance Rule in Game Theory: Resolving the Cauvery River Basin Conflict Through Strategic Equilibria", "IJRASET", "https://consensus.app/papers/details/a57c3813392a5d12af56fc85c56bda33/?utm_source=claude_code"),
      bibEntry("Wang, C. et al.", "2024", "Distributed Hydrological Modeling With Physics-Encoded Deep Learning: A General Framework and Its Application in the Amazon", "Water Resources Research", "https://consensus.app/papers/details/00c6128bc1ac5254beaccf21dd0ebd58/?utm_source=claude_code"),
      bibEntry("Willard, J. et al.", "2020", "Integrating Scientific Knowledge with Machine Learning for Engineering and Environmental Systems", "ACM Computing Surveys", "https://consensus.app/papers/details/81a68be9a0c15a76b63b76910daf89d9/?utm_source=claude_code"),

    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('doctoral_proposal_geopolitical_impunity.docx', buffer);
  console.log('Proposal saved: doctoral_proposal_geopolitical_impunity.docx');
});
