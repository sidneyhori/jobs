import Anthropic from "@anthropic-ai/sdk";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

// Load .env.local for local dev (Vercel production injects env vars automatically)
if (!process.env.ANTHROPIC_API_KEY) {
  try {
    const envPath = join(process.cwd(), ".env.local");
    if (existsSync(envPath)) {
      const lines = readFileSync(envPath, "utf-8").split("\n");
      for (const line of lines) {
        const match = line.match(/^([^#=]+)=(.*)$/);
        if (match) process.env[match[1].trim()] = match[2].trim();
      }
    }
  } catch (_) {}
}

// Load data at cold-start (cached across invocations)
const dataPath = join(process.cwd(), "us", "site", "data.json");
const summaryPath = join(process.cwd(), "us", "site", "summary.json");
let allData, summaryData;

function loadData() {
  if (!allData) {
    allData = JSON.parse(readFileSync(dataPath, "utf-8"));
    summaryData = JSON.parse(readFileSync(summaryPath, "utf-8"));
  }
}

// ── Tool definitions ──────────────────────────────────────────────────────

const tools = [
  {
    name: "query_occupations",
    description:
      "Query the US occupations dataset. Returns matching occupations with key fields. " +
      "Use this to filter, sort, and explore the data. You can call this multiple times to refine your analysis.",
    input_schema: {
      type: "object",
      properties: {
        filters: {
          type: "array",
          description: "Array of filter conditions to apply",
          items: {
            type: "object",
            properties: {
              field: {
                type: "string",
                enum: [
                  "exposure", "advantage", "growth", "opportunity",
                  "pay", "jobs", "outlook", "education",
                  "category", "slug",
                ],
                description: "Field to filter on",
              },
              op: {
                type: "string",
                enum: [">=", "<=", "==", ">", "<", "contains"],
                description: "Comparison operator. Use 'contains' for partial text match on string fields.",
              },
              value: {
                description: "Value to compare against (number or string)",
              },
            },
            required: ["field", "op", "value"],
          },
        },
        sort: {
          type: "object",
          description: "Sort the results",
          properties: {
            field: {
              type: "string",
              enum: [
                "exposure", "advantage", "growth", "opportunity",
                "pay", "jobs", "outlook",
              ],
            },
            direction: { type: "string", enum: ["asc", "desc"] },
          },
          required: ["field", "direction"],
        },
        limit: {
          type: "integer",
          description: "Max results to return (default 15, max 50)",
          default: 15,
        },
        group_by: {
          type: "string",
          enum: ["category", "education"],
          description:
            "Group results and return aggregated stats per group (avg exposure, avg pay, total workers).",
        },
        fields: {
          type: "array",
          items: { type: "string" },
          description:
            "Which fields to include in each result. Default: title, slug, jobs, pay, exposure, opportunity, advantage, growth, outlook, education.",
        },
      },
    },
  },
  {
    name: "get_summary_stats",
    description:
      "Get overall summary statistics for the entire dataset: total workers, category breakdowns, education distributions. " +
      "Use this for big-picture questions.",
    input_schema: {
      type: "object",
      properties: {
        include_categories: {
          type: "boolean",
          description: "Include per-category breakdown (default false)",
          default: false,
        },
      },
    },
  },
  {
    name: "get_occupation_detail",
    description:
      "Get full details for a specific occupation including AI rationales. " +
      "Use this when the user asks about a specific job/occupation.",
    input_schema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description:
            "Occupation name (partial match) or slug (exact match). Examples: 'accountant', 'registered-nurses', 'software'",
        },
      },
      required: ["query"],
    },
  },
];

// ── Tool execution ────────────────────────────────────────────────────────

function executeQueryTool(input) {
  loadData();
  let items = allData.filter((d) => d.jobs != null && d.jobs > 0);

  // Apply filters
  if (input.filters) {
    for (const f of input.filters) {
      items = items.filter((d) => {
        let v;
        if (f.field === "education" || f.field === "category" || f.field === "slug") {
          v = d[f.field] || "";
        } else {
          v = d[f.field];
        }
        if (v == null) return false;
        switch (f.op) {
          case ">=": return v >= f.value;
          case "<=": return v <= f.value;
          case ">": return v > f.value;
          case "<": return v < f.value;
          case "==": return typeof v === "string"
            ? v.toLowerCase() === String(f.value).toLowerCase()
            : v === f.value;
          case "contains": return typeof v === "string" &&
            v.toLowerCase().includes(String(f.value).toLowerCase());
          default: return true;
        }
      });
    }
  }

  // Group by
  if (input.group_by) {
    const groups = {};
    for (const d of items) {
      const key = d[input.group_by] || "Other";
      if (!groups[key]) {
        groups[key] = {
          group: key,
          count: 0,
          total_workers: 0,
          sum_pay_weighted: 0,
          sum_exposure_weighted: 0,
          sum_opportunity_weighted: 0,
          sum_advantage_weighted: 0,
        };
      }
      const g = groups[key];
      const emp = d.jobs || 0;
      g.count++;
      g.total_workers += emp;
      g.sum_pay_weighted += (d.pay || 0) * emp;
      g.sum_exposure_weighted += (d.exposure || 0) * emp;
      g.sum_opportunity_weighted += (d.opportunity || 0) * emp;
      g.sum_advantage_weighted += (d.advantage || 0) * emp;
    }

    let rows = Object.values(groups).map((g) => ({
      group: g.group,
      occupations: g.count,
      total_workers: g.total_workers,
      avg_pay: g.total_workers > 0
        ? Math.round(g.sum_pay_weighted / g.total_workers)
        : 0,
      avg_exposure:
        g.total_workers > 0
          ? +(g.sum_exposure_weighted / g.total_workers).toFixed(1)
          : 0,
      avg_opportunity:
        g.total_workers > 0
          ? +(g.sum_opportunity_weighted / g.total_workers).toFixed(1)
          : 0,
      avg_advantage:
        g.total_workers > 0
          ? +(g.sum_advantage_weighted / g.total_workers).toFixed(1)
          : 0,
    }));

    if (input.sort) {
      const fieldMap = {
        exposure: "avg_exposure",
        pay: "avg_pay",
        opportunity: "avg_opportunity",
        advantage: "avg_advantage",
        jobs: "total_workers",
      };
      const sf = fieldMap[input.sort.field] || "total_workers";
      const dir = input.sort.direction === "asc" ? 1 : -1;
      rows.sort((a, b) => (b[sf] - a[sf]) * dir);
    } else {
      rows.sort((a, b) => b.total_workers - a.total_workers);
    }

    return {
      total_groups: rows.length,
      total_matching_workers: items.reduce((s, d) => s + (d.jobs || 0), 0),
      total_matching_occupations: items.length,
      groups: rows,
    };
  }

  // Sort
  if (input.sort) {
    const { field, direction } = input.sort;
    items.sort((a, b) => {
      let av = a[field] != null ? a[field] : -Infinity;
      let bv = b[field] != null ? b[field] : -Infinity;
      return direction === "desc" ? bv - av : av - bv;
    });
  }

  // Limit
  const limit = Math.min(input.limit || 15, 50);
  items = items.slice(0, limit);

  // Select fields
  const defaultFields = [
    "title", "slug", "jobs", "pay", "exposure",
    "opportunity", "advantage", "growth", "outlook", "education",
  ];
  const fields = input.fields || defaultFields;

  const results = items.map((d) => {
    const row = {};
    for (const f of fields) {
      if (d[f] !== undefined) {
        row[f] = d[f];
      }
    }
    return row;
  });

  return {
    total_matching: allData.filter((d) => {
      if (!(d.jobs > 0)) return false;
      if (input.filters) {
        for (const f of input.filters) {
          const v = d[f.field];
          if (v == null) return false;
          if (f.op === ">=" && v < f.value) return false;
          if (f.op === "<=" && v > f.value) return false;
          if (f.op === "==" && v !== f.value) return false;
        }
      }
      return true;
    }).length,
    showing: results.length,
    results,
  };
}

function executeSummaryTool(input) {
  loadData();
  const totalWorkers = allData.reduce((s, d) => s + (d.jobs || 0), 0);
  const totalOccupations = allData.filter((d) => d.jobs > 0).length;

  let wExpSum = 0, wPaySum = 0, wC = 0;
  for (const d of allData) {
    const e = d.jobs || 0;
    if (e > 0) {
      wExpSum += (d.exposure || 0) * e;
      wPaySum += (d.pay || 0) * e;
      wC += e;
    }
  }

  const result = {
    total_occupations: totalOccupations,
    total_workers: totalWorkers,
    avg_exposure: wC > 0 ? +(wExpSum / wC).toFixed(1) : 0,
    avg_pay: wC > 0 ? Math.round(wPaySum / wC) : 0,
    high_risk_workers: allData
      .filter((d) => d.exposure >= 7 && d.jobs > 0)
      .reduce((s, d) => s + d.jobs, 0),
    low_risk_workers: allData
      .filter((d) => d.exposure <= 3 && d.jobs > 0)
      .reduce((s, d) => s + d.jobs, 0),
  };

  if (input.include_categories && summaryData.categories) {
    result.categories = summaryData.categories;
  }

  return result;
}

function executeDetailTool(input) {
  loadData();
  const q = input.query.toLowerCase();

  // Try exact slug match first
  let occ = allData.find((d) => d.slug === input.query);
  if (!occ) {
    // Fuzzy title match
    occ = allData.find((d) =>
      d.title.toLowerCase().includes(q)
    );
  }

  if (!occ) {
    return { error: "Occupation not found: " + input.query };
  }

  return {
    title: occ.title,
    slug: occ.slug,
    category: occ.category,
    jobs: occ.jobs,
    pay: occ.pay,
    education: occ.education,
    outlook: occ.outlook,
    outlook_desc: occ.outlook_desc,
    exposure: occ.exposure,
    exposure_rationale: occ.exposure_rationale,
    advantage: occ.advantage,
    advantage_rationale: occ.advantage_rationale,
    growth: occ.growth,
    growth_rationale: occ.growth_rationale,
    opportunity: occ.opportunity,
    url: occ.url,
  };
}

function executeTool(name, input) {
  switch (name) {
    case "query_occupations": return executeQueryTool(input);
    case "get_summary_stats": return executeSummaryTool(input);
    case "get_occupation_detail": return executeDetailTool(input);
    default: return { error: "Unknown tool: " + name };
  }
}

// ── System prompt ─────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `You are a data analyst expert on the US labor market and AI impact.

You have access to a dataset of 342 occupations from the Bureau of Labor Statistics (BLS) Occupational Outlook Handbook, covering approximately 143 million jobs in the United States.

## Data schema (per occupation)
- title: occupation name (English)
- slug: URL-friendly identifier
- category: industry sector (e.g. "computer-and-information-technology", "healthcare", "business-and-financial")
- jobs: total employees
- pay: median annual pay in USD
- education: typical education required (e.g. "Bachelor's degree", "High school diploma or equivalent", "Doctoral or professional degree")
- outlook: projected employment change (percentage, e.g. 5 means 5% growth over 10 years)
- outlook_desc: text description of outlook (e.g. "Faster than average", "Much faster than average")
- exposure: AI exposure risk score (0-10, higher = more exposed to automation)
- advantage: AI advantage score (0-10, higher = more benefit from AI tools)
- growth: AI growth score (0-10, higher = more growth potential with AI)
- opportunity: overall opportunity score (0-10, combines advantage + growth)

## Categories
architecture-and-engineering, arts-and-design, building-and-grounds-cleaning, business-and-financial, community-and-social-service, computer-and-information-technology, construction-and-extraction, education-training-and-library, entertainment-and-sports, farming-fishing-and-forestry, food-preparation-and-serving, healthcare, installation-maintenance-and-repair, legal, life-physical-and-social-science, management, math, media-and-communication, military, office-and-administrative-support, personal-care-and-service, production, protective-service, sales, transportation-and-material-moving

## Voice and style
You write like a senior data journalist at an American publication — precise, sober, editorial. Think NYT Upshot or Bloomberg.

Rules:
- Always answer in English
- Never use emojis, icons, or decorative symbols
- No bullet-point lists as primary structure — write in connected prose with short paragraphs
- Use **bold** only for key numbers (e.g. **3.8 million**) and occupation names
- Lead with the most surprising or important finding — not a summary header
- Use precise numbers in US format (1,234,567, $56,780)
- When comparing groups, state the difference plainly: "X is 40% higher than Y"
- End with one line of analytical interpretation — what does this mean, why does it matter
- Keep the total response to 3-5 short paragraphs. Density over length.
- Do not use section headers with emoji. If you use headers at all, keep them short and lowercase (e.g. "## the landscape", "## who loses most")
- Never start with "Based on the analysis" or similar preamble. Start with the finding.

## Data instructions
- Use the tools to query data — never guess or make up numbers
- You can call tools multiple times if you need to cross-reference or drill deeper
- When the user asks about a specific occupation, use get_occupation_detail
- For broad questions, use query_occupations with appropriate filters
- For overview/macro questions, start with get_summary_stats`;

// ── API handler ───────────────────────────────────────────────────────────

// Simple in-memory rate limiter (per serverless instance)
const rateMap = new Map();
const RATE_WINDOW = 60000; // 1 minute
const RATE_LIMIT = 10; // max requests per IP per window

function checkRate(ip) {
  const now = Date.now();
  const entry = rateMap.get(ip);
  if (!entry || now - entry.start > RATE_WINDOW) {
    rateMap.set(ip, { start: now, count: 1 });
    return true;
  }
  entry.count++;
  return entry.count <= RATE_LIMIT;
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  // Rate limiting
  const ip = req.headers["x-forwarded-for"]?.split(",")[0]?.trim() || "unknown";
  if (!checkRate(ip)) {
    return res.status(429).json({ error: "Too many requests. Please wait a moment." });
  }

  const { question } = req.body;
  if (!question || typeof question !== "string" || question.trim().length === 0) {
    return res.status(400).json({ error: "Missing question" });
  }

  // Input length limit
  if (question.length > 500) {
    return res.status(400).json({ error: "Question too long (maximum 500 characters)." });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: "Service unavailable." });
  }

  const client = new Anthropic({ apiKey });

  try {
    let messages = [{ role: "user", content: question.trim() }];

    // Agentic loop — let Claude call tools until it has a final answer
    const maxIterations = 6;
    for (let i = 0; i < maxIterations; i++) {
      const response = await client.messages.create({
        model: "claude-sonnet-4-6",
        max_tokens: 2048,
        system: SYSTEM_PROMPT,
        tools,
        messages,
      });

      // Check if Claude wants to use tools
      if (response.stop_reason === "tool_use") {
        // Execute all tool calls
        const toolResults = [];
        for (const block of response.content) {
          if (block.type === "tool_use") {
            const result = executeTool(block.name, block.input);
            toolResults.push({
              type: "tool_result",
              tool_use_id: block.id,
              content: JSON.stringify(result),
            });
          }
        }

        // Add assistant response and tool results to conversation
        messages.push({ role: "assistant", content: response.content });
        messages.push({ role: "user", content: toolResults });
      } else {
        // Final text response — extract and return
        const text = response.content
          .filter((b) => b.type === "text")
          .map((b) => b.text)
          .join("\n");

        return res.status(200).json({ answer: text });
      }
    }

    return res.status(200).json({
      answer: "Sorry, I couldn't complete the analysis. Please try rephrasing your question.",
    });
  } catch (err) {
    console.error("API error:", err.message);
    return res.status(500).json({
      error: "Error processing your question. Please try again.",
    });
  }
}
