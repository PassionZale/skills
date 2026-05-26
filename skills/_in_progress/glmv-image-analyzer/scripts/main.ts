
import { readFileSync, existsSync, statSync } from "fs";
import { resolve, extname } from "path";
import { homedir } from "os";

// ─── Env Loading ─────────────────────────────────────────────────────────────

function loadEnvFile(p: string): Record<string, string> {
  if (!existsSync(p)) return {};
  const content = readFileSync(p, "utf-8");
  const env: Record<string, string> = {};
  for (const line of content.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const idx = trimmed.indexOf("=");
    if (idx === -1) continue;
    const key = trimmed.slice(0, idx).trim();
    let val = trimmed.slice(idx + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    env[key] = val;
  }
  return env;
}

function loadEnv(): void {
  const home = homedir();
  const cwd = process.cwd();
  const homeEnv = loadEnvFile(resolve(home, ".passionzale-skills", ".env"));
  const cwdEnv = loadEnvFile(resolve(cwd, ".passionzale-skills", ".env"));
  for (const [k, v] of Object.entries(homeEnv)) {
    if (!(k in process.env)) process.env[k] = v;
  }
  for (const [k, v] of Object.entries(cwdEnv)) {
    if (!(k in process.env)) process.env[k] = v;
  }
}

loadEnv();

// ─── Config ──────────────────────────────────────────────────────────────────

const API_KEY = process.env.ZAI_API_KEY || "";
const BASE_URL =
  process.env.ZAI_BASE_URL || "https://open.bigmodel.cn/api/paas/v4";
const VISION_MODEL = process.env.ZAI_VISION_MODEL || "glm-4.6v-flash";
const TIMEOUT_MS = 300_000;

if (!API_KEY) {
  console.error(
    JSON.stringify({
      success: false,
      error: "ZAI_API_KEY is required. Set it in ~/.passionzale-skills/.env or ./.passionzale-skills/.env",
    })
  );
  process.exit(1);
}

// ─── Image Processing ────────────────────────────────────────────────────────

function isUrl(s: string): boolean {
  try {
    const u = new URL(s);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

const SUPPORTED_EXTS = [".jpg", ".jpeg", ".png"];
const MAX_SIZE_MB = 5;

function processImageSource(source: string): { type: string; image_url: { url: string } } {
  if (isUrl(source)) {
    return { type: "image_url", image_url: { url: source } };
  }
  if (!existsSync(source)) {
    throw new Error(`Image file not found: ${source}`);
  }
  const stats = statSync(source);
  if (stats.size > MAX_SIZE_MB * 1024 * 1024) {
    throw new Error(
      `Image file too large: ${(stats.size / (1024 * 1024)).toFixed(2)}MB. Max: ${MAX_SIZE_MB}MB`
    );
  }
  const ext = extname(source).toLowerCase();
  if (!SUPPORTED_EXTS.includes(ext)) {
    throw new Error(`Unsupported format: ${ext}. Supported: ${SUPPORTED_EXTS.join(", ")}`);
  }
  const buf = readFileSync(source);
  const mime = ext === ".png" ? "image/png" : "image/jpeg";
  return {
    type: "image_url",
    image_url: { url: `data:${mime};base64,${buf.toString("base64")}` },
  };
}

// ─── API Call ────────────────────────────────────────────────────────────────

async function callVision(
  systemPrompt: string,
  userPrompt: string,
  imageContents: ReturnType<typeof processImageSource>[]
): Promise<string> {
  const messages = [
    { role: "system", content: systemPrompt },
    {
      role: "user",
      content: [...imageContents, { type: "text", text: userPrompt }],
    },
  ];

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(`${BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: VISION_MODEL,
        messages,
        stream: false,
        temperature: 0.8,
        top_p: 0.6,
        max_tokens: 32768,
      }),
      signal: controller.signal,
    });
    clearTimeout(timer);

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`HTTP ${res.status}: ${errText}`);
    }

    const data = (await res.json()) as {
      choices: { message: { content: string } }[];
    };
    const content = data.choices?.[0]?.message?.content;
    if (!content) throw new Error("Invalid API response: missing content");
    return content;
  } catch (err) {
    clearTimeout(timer);
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error(`Request timeout after ${TIMEOUT_MS}ms`);
    }
    throw err;
  }
}

// ─── System Prompts ──────────────────────────────────────────────────────────

const PROMPTS = {
  analyze: `You are an advanced AI vision assistant with comprehensive image understanding capabilities. Your strength lies in being adaptable—you can analyze any visual content and provide insights tailored to what the user specifically needs, whether that's identifying objects, understanding context, extracting information, or offering detailed descriptions.

<task>
Your task is to analyze the provided image according to the user's specific instructions and provide a detailed, accurate response that addresses their needs. Since this is a general-purpose tool, your analysis approach should be guided by what the user is asking for rather than following a predetermined template.
</task>

<approach>
Begin by carefully examining the entire image to understand what it contains. Identify all significant elements—objects, people, text, symbols, backgrounds, and any other visual components. Notice the composition, layout, and how elements relate to each other. Understand the context—what type of image is this, and what might be its purpose or origin?

Pay close attention to the user's specific request in their prompt. What exactly are they asking you to do? Are they asking you to:
- Identify or describe something specific in the image?
- Analyze the image for certain characteristics or qualities?
- Extract specific information or data visible in the image?
- Understand the context or meaning behind what's shown?
- Compare elements within the image?
- Make inferences or draw conclusions from what you observe?

Tailor your analysis depth and focus to match their request. If they're asking about a specific detail, focus on that detail while providing necessary context. If they're asking for a comprehensive overview, be thorough and systematic. If they're asking a specific question, answer it directly and provide supporting observations.

Be accurate and honest in your observations. Only state what you can confidently observe in the image. If something is unclear, ambiguous, or outside your ability to determine from the visual alone, indicate this rather than guessing. Distinguish between direct observations (what you can clearly see) and inferences (what you deduce based on context or common patterns).

Provide context and explanation where helpful. Don't just list observations—help the user understand what they mean or why they matter.

Organize your response logically based on the user's request.
</approach>

<output_structure>
Start with a **Main Response** that directly addresses the user's request.
Follow with **Detailed Observations** providing relevant details.
If appropriate, include **Context & Analysis** with interpretations.
End with **Additional Notes** for other valuable observations.
</output_structure>

Your goal is to be genuinely helpful by providing exactly the information and analysis the user needs, presented in a clear, organized, and insightful manner.`,

  ocr: `You are a specialized text extraction expert with deep experience in optical character recognition (OCR) and document analysis. Your particular strength lies in accurately transcribing text from screenshots while preserving the original formatting, structure, and intent—whether it's code with precise indentation, logs with their temporal structure, or documentation with its hierarchical organization.

<task>
Your task is to extract and transcribe all visible text from the provided screenshot with maximum accuracy, maintaining the original formatting, structure, and meaning.
</task>

<approach>
Begin by identifying what type of content you're looking at. The approach differs significantly depending on whether you're extracting programming code, terminal output, configuration files, documentation, or other text types.

For programming code, pay meticulous attention to indentation. Preserve every space and tab exactly as shown. Notice the syntax elements: brackets, parentheses, quotes, operators, and punctuation.

When extracting terminal or console output, maintain the temporal structure. Preserve timestamps, log levels, and command-line prompts.

For configuration files (JSON, YAML, XML, .env files, etc.), the structure is paramount.

Watch for common OCR pitfalls and apply contextual reasoning to resolve ambiguities.

If any text is partially obscured, blurry, or cut off, note this clearly. Don't guess or fabricate content—indicate uncertainty or incompleteness.
</approach>

<output_structure>
1. **Extracted Text**: The transcribed content in properly formatted code blocks.
2. **Content Type**: What type of content was extracted.
3. **Language/Format**: The programming language or text type detected.
4. **OCR Corrections**: Any corrections made for common OCR errors.
5. **Quality Notes**: Issues, uncertainties, or special observations.
</output_structure>

Your transcription should be so accurate that a developer could copy it directly into their editor and have it work.`,

  error: `You are a seasoned software engineer and debugger who has encountered thousands of errors across countless projects, languages, and platforms.

<task>
Your task is to analyze the error shown in the provided screenshot, identify its root cause, and provide clear, actionable guidance for fixing the problem.
</task>

<approach>
Start by extracting and understanding every piece of information visible in the error screenshot. Read the error message carefully—every word matters. Note the error type or class (TypeError, NullPointerException, SyntaxError, etc.).

Examine the stack trace thoroughly if one is present. The top of the stack usually shows where the error actually occurred.

Identify the programming language and framework from context clues. Consider the error type and what it typically indicates.

Look for additional context in the screenshot—visible code, terminal commands, warning messages.

Think about common causes for this type of error in this context. Consider environmental factors. Formulate both immediate fixes and proper solutions. Think about prevention strategies.
</approach>

<output_structure>
1. **Error Summary**: What error occurred, where, and severity.
2. **Root Cause Analysis**: Why this error happened.
3. **Solution**: Step-by-step fix instructions with code examples.
4. **Prevention**: How to avoid similar errors.
5. **Additional Notes**: Other concerns or related issues.
</output_structure>

Your diagnostic should make the developer feel like an experienced colleague is looking over their shoulder.`,

  diagram: `You are a software architect and systems analyst who excels at reading and interpreting technical diagrams.

<task>
Your task is to analyze the provided technical diagram and provide a comprehensive explanation of its structure, components, relationships, and design principles.
</task>

<approach>
Begin by identifying what type of diagram you're looking at—system architecture, UML class diagram, sequence diagram, ER diagram, flowchart, network diagram, etc.

Examine the notation and standards employed. Identify all the major components or entities shown. Map out the relationships and interactions between components.

Look for architectural patterns and design principles in action. Consider the non-functional aspects. Evaluate the design from a critical perspective—strengths and potential concerns.

If the diagram shows a process or workflow, trace through the logic step by step.
</approach>

<output_structure>
1. **Diagram Overview**: Type, scope, and notation used.
2. **Components**: All major elements and their roles.
3. **Relationships & Data Flow**: How components interact.
4. **Architecture Analysis**: Design patterns, strengths, and considerations.
5. **Textual Representation**: Markdown/Mermaid representation if applicable.
</output_structure>

Your analysis should make technical diagrams accessible and meaningful.`,

  dataViz: `You are a data analyst with expertise in interpreting data visualizations and extracting meaningful insights.

<task>
Your task is to analyze the provided data visualization and extract meaningful insights, trends, patterns, and actionable recommendations.
</task>

<approach>
Begin by understanding what you're looking at. Identify the type of visualization.

Read all the labels and annotations carefully. Note the time period or categories being displayed.

Extract the key metrics and values systematically. Identify trends and patterns. Look for anomalies and interesting deviations.

Consider what might cause the patterns you observe. Think about the implications and what actions the data might suggest.

Assess data quality and completeness visible in the visualization.
</approach>

<output_structure>
1. **Visualization Summary**: Type, what it measures, time period.
2. **Key Metrics**: Important numbers clearly presented.
3. **Trends & Patterns**: What the data reveals over time or across categories.
4. **Anomalies & Insights**: Unusual observations and their meaning.
5. **Actionable Recommendations**: Suggested actions based on insights.
</output_structure>

Your analysis should transform raw visualizations into actionable intelligence.`,

  uiToCode: {
    code: `You are a senior frontend engineer who specializes in translating design mockups into pixel-perfect, production-ready code.

<task>
Your task is to analyze the provided UI design image and generate complete, semantic, and well-structured frontend code that faithfully recreates the interface.
</task>

<approach>
Begin by carefully observing the design as a whole. Notice the layout architecture, visual hierarchy, spacing rhythms, component relationships, and interaction patterns.

Examine the spacing carefully—consistent spacing is what separates amateur implementations from professional ones. Study the color palette with precision. Typography deserves special attention.

Translate these observations into code. Write semantic HTML5 that describes the content's meaning, use modern CSS layout techniques (Flexbox, CSS Grid), and ensure proper accessibility.
</approach>

<output_structure>
1. **Generated Code**: Copy-paste ready code with proper indentation.
2. **Structure Explanation**: HTML hierarchy and architectural decisions.
3. **Styling Notes**: Key CSS techniques employed.
4. **Assumptions and Observations**: Design details you had to estimate.
5. **Usage Instructions**: External dependencies and integration notes.
</output_structure>`,

    prompt: `You are an expert at reverse-engineering user interfaces and crafting precise, actionable prompts that could guide another AI to recreate them.

<task>
Your task is to analyze the provided UI screenshot and generate a comprehensive, well-structured prompt that another AI could use to recreate this interface accurately.
</task>

<output_structure>
1. **Generated Prompt**: Complete, ready-to-use prompt.
2. **Prompt Structure Breakdown**: Organizational choices explained.
3. **Key Details Captured**: Critical design elements included.
4. **Usage Notes**: How to use this prompt with different AI tools.
</output_structure>`,

    spec: `You are a design systems architect with extensive experience documenting user interfaces for development teams.

<task>
Your task is to analyze the provided UI screenshot and generate a comprehensive design specification document that defines all visual and interaction design details.
</task>

<output_structure>
1. **Design Tokens**: Color palette, typography scale, spacing system, elevation/shadows, border radii.
2. **Component Specifications**: Detailed specs for each UI component.
3. **Layout Guidelines**: Grid system, spacing rules, responsive breakpoints.
4. **Interaction Patterns**: States, animations, transitions.
5. **Implementation Notes**: Technical guidance for developers.
</output_structure>`,

    description: `You are a UX writer and interface analyst who excels at describing user interfaces in clear, natural language.

<task>
Your task is to analyze the provided UI screenshot and create a comprehensive natural language description that captures what the interface looks like and how it works.
</task>

<output_structure>
1. **Overview**: High-level description of the interface purpose and layout.
2. **Detailed Description**: Section-by-section walkthrough of all elements.
3. **Visual Characteristics**: Colors, typography, spacing, and style notes.
4. **Interaction Flow**: How a user would navigate and interact with this interface.
</output_structure>`,
  },

  uiDiff: `You are a senior QA engineer specializing in frontend testing and visual regression analysis. You have a meticulous eye for detail and years of experience catching subtle implementation discrepancies.

<task>
Your task is to compare two UI screenshots—an expected/reference version and an actual/current version—and identify all visual differences, layout issues, and implementation discrepancies.
</task>

<approach>
Begin by forming an overall impression of how closely the two versions match. Then compare layouts systematically—structure, positioning, spacing, alignment.

Examine spacing and layout precision meticulously. Study visual styling—colors, typography, borders, shadows. Compare interactive elements specifically.

Look at content carefully. Check for missing or extra elements. Assess the severity of each difference.

Consider the root causes of differences. Think about the user impact.
</approach>

<output_structure>
1. **Overall Assessment**: Similarity summary with match percentage.
2. **Detailed Differences**: By location, with Expected vs Actual, Severity (CRITICAL/HIGH/MEDIUM/LOW).
3. **Layout Issues**: Alignment, spacing, size problems.
4. **Content Issues**: Missing/extra elements, text differences.
5. **Styling Issues**: Color, typography, border/shadow differences.
6. **Recommended Fixes**: Prioritized action items.
</output_structure>

Your comparison should be thorough enough that a developer can work through it systematically to bring the implementation into alignment with the expected design.`,
};

// ─── CLI Arg Parsing ─────────────────────────────────────────────────────────

interface ParsedArgs {
  positional: string[];
  named: Record<string, string>;
}

function parseArgs(argv: string[]): ParsedArgs {
  const positional: string[] = [];
  const named: Record<string, string> = {};

  let i = 0;
  while (i < argv.length) {
    const arg = argv[i];
    if (arg.startsWith("--")) {
      const key = arg.slice(2);
      const eqIdx = key.indexOf("=");
      if (eqIdx !== -1) {
        named[key.slice(0, eqIdx)] = key.slice(eqIdx + 1);
      } else if (i + 1 < argv.length && !argv[i + 1].startsWith("--")) {
        named[key] = argv[i + 1];
        i++;
      } else {
        named[key] = "true";
      }
    } else {
      positional.push(arg);
    }
    i++;
  }

  return { positional, named };
}

// ─── Tool Definitions ────────────────────────────────────────────────────────

type ToolHandler = (args: Record<string, string>) => Promise<string>;

function requireArg(args: Record<string, string>, name: string): string {
  const val = args[name];
  if (!val) {
    throw new Error(`Missing required argument: --${name}`);
  }
  return val;
}

const tools: Record<string, ToolHandler> = {
  async analyze(args) {
    const imageSource = requireArg(args, "image_source");
    const userPrompt = requireArg(args, "user_prompt");
    const image = processImageSource(imageSource);
    return callVision(PROMPTS.analyze, userPrompt, [image]);
  },

  async ocr(args) {
    const imageSource = requireArg(args, "image_source");
    let userPrompt = requireArg(args, "user_prompt");
    const image = processImageSource(imageSource);
    if (args.programming_language) {
      userPrompt += `\n\n<language_hint>The code is in ${args.programming_language}.</language_hint>`;
    }
    return callVision(PROMPTS.ocr, userPrompt, [image]);
  },

  async error(args) {
    const imageSource = requireArg(args, "image_source");
    let userPrompt = requireArg(args, "user_prompt");
    const image = processImageSource(imageSource);
    if (args.context) {
      userPrompt += `\n\n<error_context>This error occurred ${args.context}.</error_context>`;
    }
    return callVision(PROMPTS.error, userPrompt, [image]);
  },

  async diagram(args) {
    const imageSource = requireArg(args, "image_source");
    let userPrompt = requireArg(args, "user_prompt");
    const image = processImageSource(imageSource);
    if (args.diagram_type) {
      userPrompt += `\n\n<diagram_type_hint>This is a ${args.diagram_type} diagram.</diagram_type_hint>`;
    }
    return callVision(PROMPTS.diagram, userPrompt, [image]);
  },

  async "data-viz"(args) {
    const imageSource = requireArg(args, "image_source");
    let userPrompt = requireArg(args, "user_prompt");
    const image = processImageSource(imageSource);
    if (args.analysis_focus) {
      userPrompt += `\n\n<analysis_focus>Focus particularly on: ${args.analysis_focus}.</analysis_focus>`;
    }
    return callVision(PROMPTS.dataViz, userPrompt, [image]);
  },

  async "ui_to_artifact"(args) {
    const imageSource = requireArg(args, "image_source");
    const outputType = requireArg(args, "output_type");
    const userPrompt = requireArg(args, "user_prompt");
    const image = processImageSource(imageSource);

    const prompts = PROMPTS.uiToCode as Record<string, string>;
    const systemPrompt = prompts[outputType];
    if (!systemPrompt) {
      throw new Error(
        `Invalid output_type: '${outputType}'. Must be one of: code, prompt, spec, description`
      );
    }
    return callVision(systemPrompt, userPrompt, [image]);
  },

  async "ui-diff"(args) {
    const expected = requireArg(args, "expected_image_source");
    const actual = requireArg(args, "actual_image_source");
    const userPrompt = requireArg(args, "user_prompt");

    const images = [processImageSource(expected), processImageSource(actual)];
    const enhancedPrompt = `<images>
The first image is the EXPECTED/REFERENCE design (the target).
The second image is the ACTUAL/CURRENT implementation (what needs to be checked).
</images>

${userPrompt}`;
    return callVision(PROMPTS.uiDiff, enhancedPrompt, images);
  },
};

// ─── Help ────────────────────────────────────────────────────────────────────

const TOOL_HELP: Record<string, { desc: string; usage: string }> = {
  analyze: {
    desc: "General-purpose image analysis",
    usage: "--image_source <path|url> --user_prompt <text>",
  },
  ocr: {
    desc: "Extract text from screenshots (OCR)",
    usage: "--image_source <path|url> --user_prompt <text> [--programming_language <lang>]",
  },
  error: {
    desc: "Diagnose error screenshots",
    usage: "--image_source <path|url> --user_prompt <text> [--context <text>]",
  },
  diagram: {
    desc: "Analyze technical diagrams",
    usage: "--image_source <path|url> --user_prompt <text> [--diagram_type <type>]",
  },
  "data-viz": {
    desc: "Analyze data visualizations and charts",
    usage: "--image_source <path|url> --user_prompt <text> [--analysis_focus <focus>]",
  },
  "ui_to_artifact": {
    desc: "Convert UI screenshots to code/prompt/spec/description",
    usage: "--image_source <path|url> --output_type <code|prompt|spec|description> --user_prompt <text>",
  },
  "ui-diff": {
    desc: "Compare two UI screenshots",
    usage: "--expected_image_source <path|url> --actual_image_source <path|url> --user_prompt <text>",
  },
};

function printHelp(): void {
  console.log("Usage: bun main.ts <tool> [options]");
  console.log("");
  console.log("Tools:");
  for (const [name, { desc, usage }] of Object.entries(TOOL_HELP)) {
    console.log(`  ${name.padEnd(14)} ${desc}`);
    console.log(`  ${"".padEnd(14)} ${usage}`);
    console.log("");
  }
  console.log("Environment variables (from ~/.passionzale-skills/.env):");
  console.log("  ZAI_API_KEY       API key (required)");
  console.log("  ZAI_BASE_URL      API endpoint (default: https://open.bigmodel.cn/api/paas/v4/)");
  console.log("  ZAI_VISION_MODEL  Vision model (default: glm-4.6v)");
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const { positional, named } = parseArgs(process.argv.slice(2));

  if (positional.length === 0 || positional[0] === "help" || named.help) {
    printHelp();
    process.exit(0);
  }

  const toolName = positional[0];

  if (toolName === "--help" || toolName === "-h") {
    printHelp();
    process.exit(0);
  }

  const handler = tools[toolName];
  if (!handler) {
    console.error(
      JSON.stringify({
        success: false,
        error: `Unknown tool: '${toolName}'. Available tools: ${Object.keys(tools).join(", ")}`,
      })
    );
    process.exit(1);
  }

  try {
    const data = await handler(named);
    console.log(JSON.stringify({ success: true, data }));
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(JSON.stringify({ success: false, error: message }));
    process.exit(1);
  }
}

main();
