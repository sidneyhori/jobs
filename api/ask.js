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
const dataPath = join(process.cwd(), "brazil", "site", "data.json");
const summaryPath = join(process.cwd(), "brazil", "site", "summary.json");
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
      "Query the Brazilian occupations dataset. Returns matching occupations with key fields. " +
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
                  "exposicao", "vantagem", "crescimento", "oportunidade",
                  "salario", "empregados", "saldo", "escolaridade",
                  "grande_grupo", "codigo",
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
                "exposicao", "vantagem", "crescimento", "oportunidade",
                "salario", "empregados", "saldo",
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
          enum: ["grande_grupo", "escolaridade"],
          description:
            "Group results and return aggregated stats per group (avg exposure, avg salary, total workers, net balance).",
        },
        demographic_filter: {
          type: "object",
          description: "Filter by demographic breakdown within occupations",
          properties: {
            field: {
              type: "string",
              enum: [
                "total_feminino", "total_masculino",
                "total_branca", "total_negra", "total_preta", "total_parda",
              ],
              description: "Demographic field from occupation demographics object",
            },
            min_pct: {
              type: "number",
              description: "Minimum percentage of this demographic within the occupation (0-100)",
            },
          },
          required: ["field"],
        },
        uf_code: {
          type: "string",
          description:
            "Filter to occupations present in a specific state. Use 2-digit IBGE code (e.g. '35' for SP, '33' for RJ). " +
            "When filtering by UF, empregados and salario come from that state's data.",
        },
        fields: {
          type: "array",
          items: { type: "string" },
          description:
            "Which fields to include in each result. Default: titulo, codigo, empregados, salario, exposicao, oportunidade, vantagem, crescimento, saldo, escolaridade.",
        },
      },
    },
  },
  {
    name: "get_summary_stats",
    description:
      "Get overall summary statistics for the entire dataset: total workers, demographic breakdowns by gender and race, " +
      "and per-state aggregates. Use this for big-picture questions.",
    input_schema: {
      type: "object",
      properties: {
        include_states: {
          type: "boolean",
          description: "Include per-state breakdown (default false)",
          default: false,
        },
      },
    },
  },
  {
    name: "get_occupation_detail",
    description:
      "Get full details for a specific occupation including AI rationales, demographic breakdown, and state-level data. " +
      "Use this when the user asks about a specific job/occupation.",
    input_schema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description:
            "Occupation name (partial match) or CBO code (exact match). Examples: 'enfermeiro', '2235', 'motorista'",
        },
      },
      required: ["query"],
    },
  },
];

// ── Tool execution ────────────────────────────────────────────────────────

function executeQueryTool(input) {
  loadData();
  let items = allData.filter((d) => d.empregados != null && d.empregados > 0);

  const ufCode = input.uf_code || null;

  // Apply filters
  if (input.filters) {
    for (const f of input.filters) {
      items = items.filter((d) => {
        let v;
        if (f.field === "escolaridade" || f.field === "grande_grupo" || f.field === "codigo") {
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

  // UF filter
  if (ufCode) {
    items = items.filter((d) => d.por_uf && d.por_uf[ufCode]);
  }

  // Demographic filter
  if (input.demographic_filter) {
    const df = input.demographic_filter;
    items = items.filter((d) => {
      if (!d.demographics) return false;
      const demVal = d.demographics[df.field] || 0;
      const totalDem =
        (d.demographics.total_feminino || 0) +
        (d.demographics.total_masculino || 0);
      if (totalDem === 0) return false;
      if (df.min_pct) {
        return (demVal / totalDem) * 100 >= df.min_pct;
      }
      return demVal > 0;
    });
  }

  // Group by
  if (input.group_by) {
    const groups = {};
    for (const d of items) {
      const key = d[input.group_by] || "Outros";
      if (!groups[key]) {
        groups[key] = {
          group: key,
          count: 0,
          total_workers: 0,
          sum_salary_weighted: 0,
          sum_exposicao_weighted: 0,
          sum_oportunidade_weighted: 0,
          sum_vantagem_weighted: 0,
          sum_saldo: 0,
        };
      }
      const g = groups[key];
      const emp = d.empregados || 0;
      g.count++;
      g.total_workers += emp;
      g.sum_salary_weighted += (d.salario || 0) * emp;
      g.sum_exposicao_weighted += (d.exposicao || 0) * emp;
      g.sum_oportunidade_weighted += (d.oportunidade || 0) * emp;
      g.sum_vantagem_weighted += (d.vantagem || 0) * emp;
      g.sum_saldo += d.saldo || 0;
    }

    let rows = Object.values(groups).map((g) => ({
      group: g.group,
      occupations: g.count,
      total_workers: g.total_workers,
      avg_salary: g.total_workers > 0
        ? Math.round(g.sum_salary_weighted / g.total_workers)
        : 0,
      avg_exposicao:
        g.total_workers > 0
          ? +(g.sum_exposicao_weighted / g.total_workers).toFixed(1)
          : 0,
      avg_oportunidade:
        g.total_workers > 0
          ? +(g.sum_oportunidade_weighted / g.total_workers).toFixed(1)
          : 0,
      avg_vantagem:
        g.total_workers > 0
          ? +(g.sum_vantagem_weighted / g.total_workers).toFixed(1)
          : 0,
      net_balance: g.sum_saldo,
    }));

    if (input.sort) {
      const fieldMap = {
        exposicao: "avg_exposicao",
        salario: "avg_salary",
        oportunidade: "avg_oportunidade",
        vantagem: "avg_vantagem",
        empregados: "total_workers",
        saldo: "net_balance",
      };
      const sf = fieldMap[input.sort.field] || "total_workers";
      const dir = input.sort.direction === "asc" ? 1 : -1;
      rows.sort((a, b) => (b[sf] - a[sf]) * dir);
    } else {
      rows.sort((a, b) => b.total_workers - a.total_workers);
    }

    return {
      total_groups: rows.length,
      total_matching_workers: items.reduce((s, d) => s + (d.empregados || 0), 0),
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
      if (ufCode && (field === "empregados" || field === "salario")) {
        av = a.por_uf?.[ufCode]?.[field === "empregados" ? "ativos" : "salario_mediano"] ?? -Infinity;
        bv = b.por_uf?.[ufCode]?.[field === "empregados" ? "ativos" : "salario_mediano"] ?? -Infinity;
      }
      return direction === "desc" ? bv - av : av - bv;
    });
  }

  // Limit
  const limit = Math.min(input.limit || 15, 50);
  items = items.slice(0, limit);

  // Select fields
  const defaultFields = [
    "titulo", "codigo", "empregados", "salario", "exposicao",
    "oportunidade", "vantagem", "crescimento", "saldo", "escolaridade",
  ];
  const fields = input.fields || defaultFields;

  const results = items.map((d) => {
    const row = {};
    for (const f of fields) {
      if (f === "demographics" && d.demographics) {
        row.demographics = d.demographics;
      } else if (f === "grande_grupo") {
        row.grande_grupo = d.grande_grupo;
      } else if (d[f] !== undefined) {
        row[f] = d[f];
      }
    }
    // If UF-filtered, add state-specific data
    if (ufCode && d.por_uf?.[ufCode]) {
      row._uf_ativos = d.por_uf[ufCode].ativos;
      row._uf_salario = d.por_uf[ufCode].salario_mediano;
    }
    return row;
  });

  return {
    total_matching: allData.filter((d) => {
      // Re-run filters to count (simplified)
      if (!(d.empregados > 0)) return false;
      if (input.filters) {
        for (const f of input.filters) {
          const v = d[f.field];
          if (v == null) return false;
          if (f.op === ">=" && v < f.value) return false;
          if (f.op === "<=" && v > f.value) return false;
          if (f.op === "==" && v !== f.value) return false;
        }
      }
      if (ufCode && !(d.por_uf && d.por_uf[ufCode])) return false;
      return true;
    }).length,
    showing: results.length,
    results,
  };
}

function executeSummaryTool(input) {
  loadData();
  const totalWorkers = allData.reduce((s, d) => s + (d.empregados || 0), 0);
  const totalOccupations = allData.filter((d) => d.empregados > 0).length;

  let wExpSum = 0, wSalSum = 0, wC = 0;
  for (const d of allData) {
    const e = d.empregados || 0;
    if (e > 0) {
      wExpSum += (d.exposicao || 0) * e;
      wSalSum += (d.salario || 0) * e;
      wC += e;
    }
  }

  const result = {
    total_occupations: totalOccupations,
    total_workers: totalWorkers,
    avg_exposicao: wC > 0 ? +(wExpSum / wC).toFixed(1) : 0,
    avg_salary: wC > 0 ? Math.round(wSalSum / wC) : 0,
    demographics: summaryData.demographics || {},
    high_risk_workers: allData
      .filter((d) => d.exposicao >= 7 && d.empregados > 0)
      .reduce((s, d) => s + d.empregados, 0),
    low_risk_workers: allData
      .filter((d) => d.exposicao <= 3 && d.empregados > 0)
      .reduce((s, d) => s + d.empregados, 0),
  };

  if (input.include_states && summaryData.por_uf) {
    const states = [];
    for (const [code, s] of Object.entries(summaryData.por_uf)) {
      states.push({
        code,
        abbr: summaryData.uf_codes?.[code] || code,
        name: s.nome,
        workers: s.total_workers,
        avg_salary: Math.round(s.avg_salary),
        avg_exposicao: +s.avg_exposicao.toFixed(1),
      });
    }
    states.sort((a, b) => b.workers - a.workers);
    result.states = states;
  }

  return result;
}

function executeDetailTool(input) {
  loadData();
  const q = input.query.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

  // Try exact code match first
  let occ = allData.find((d) => d.codigo === input.query);
  if (!occ) {
    // Fuzzy title match
    occ = allData.find((d) =>
      d.titulo.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").includes(q)
    );
  }

  if (!occ) {
    return { error: "Occupation not found: " + input.query };
  }

  const result = {
    titulo: occ.titulo,
    codigo: occ.codigo,
    grande_grupo: occ.grande_grupo,
    empregados: occ.empregados,
    salario: occ.salario,
    escolaridade: occ.escolaridade,
    saldo: occ.saldo,
    exposicao: occ.exposicao,
    exposicao_rationale: occ.exposicao_rationale,
    vantagem: occ.vantagem,
    vantagem_rationale: occ.vantagem_rationale,
    crescimento: occ.crescimento,
    crescimento_rationale: occ.crescimento_rationale,
    oportunidade: occ.oportunidade,
  };

  if (occ.demographics) result.demographics = occ.demographics;

  if (occ.por_uf) {
    const topStates = Object.entries(occ.por_uf)
      .map(([code, s]) => ({
        abbr: summaryData.uf_codes?.[code] || code,
        ativos: s.ativos,
        salario: s.salario_mediano,
      }))
      .sort((a, b) => b.ativos - a.ativos)
      .slice(0, 10);
    result.top_states = topStates;
  }

  return result;
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

const SYSTEM_PROMPT = `You are a data analyst expert on the Brazilian labor market and AI impact.

You have access to a dataset of 626 occupations from the CBO (Classificação Brasileira de Ocupações), covering approximately 19 million formal jobs registered in RAIS/CAGED.

## Data schema (per occupation)
- titulo: occupation name (Portuguese)
- codigo: 4-digit CBO code
- grande_grupo: industry sector (e.g. "CIÊNCIAS E ARTES", "SERVIÇOS ADMINISTRATIVOS")
- empregados: total formal employees
- salario: median monthly salary in R$
- escolaridade: modal education level (Analfabeto, Até 5ª Incompleto, 6ª a 9ª Fundamental, Médio Completo, Superior Completo, Mestrado, Doutorado)
- saldo: net CAGED job balance (positive = net hiring, negative = net layoffs)
- exposicao: AI exposure risk score (0-10, higher = more exposed to automation)
- vantagem: AI advantage score (0-10, higher = more benefit from AI tools)
- crescimento: AI growth score (0-10, higher = more growth potential with AI)
- oportunidade: overall opportunity score (0-10, combines vantagem + crescimento)
- demographics: {total_feminino, total_masculino, total_branca, total_negra, total_preta, total_parda}
- por_uf: per-state data with {ativos, salario_mediano} per IBGE state code

## UF codes (Brazilian states)
11=RO, 12=AC, 13=AM, 14=RR, 15=PA, 16=AP, 17=TO, 21=MA, 22=PI, 23=CE, 24=RN, 25=PB, 26=PE, 27=AL, 28=SE, 29=BA, 31=MG, 32=ES, 33=RJ, 35=SP, 41=PR, 42=SC, 43=RS, 50=MS, 51=MT, 52=GO, 53=DF

## Voice and style
You write like a senior data journalist at a Brazilian investigative publication — precise, sober, editorial. Think Folha de S.Paulo's data desk or Piauí magazine.

Rules:
- Always answer in Brazilian Portuguese
- Never use emojis, icons, or decorative symbols
- No bullet-point lists as primary structure — write in connected prose with short paragraphs
- Use **bold** only for key numbers (e.g. **3,8 milhões**) and occupation names
- Lead with the most surprising or important finding — not a summary header
- Use precise numbers in Brazilian format (1.234.567, R$ 3.456,78)
- When comparing groups, state the difference plainly: "X é 40% maior que Y"
- End with one line of analytical interpretation — what does this mean, why does it matter
- Keep the total response to 3-5 short paragraphs. Density over length.
- Do not use section headers with emoji. If you use headers at all, keep them short and lowercase (e.g. "## o cenário", "## quem mais perde")
- Never start with "Com base na análise" or similar preamble. Start with the finding.

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
    return res.status(429).json({ error: "Muitas requisições. Aguarde um momento." });
  }

  const { question } = req.body;
  if (!question || typeof question !== "string" || question.trim().length === 0) {
    return res.status(400).json({ error: "Missing question" });
  }

  // Input length limit
  if (question.length > 500) {
    return res.status(400).json({ error: "Pergunta muito longa (máximo 500 caracteres)." });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: "Serviço indisponível." });
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
      answer: "Desculpe, não consegui completar a análise. Tente reformular sua pergunta.",
    });
  } catch (err) {
    console.error("API error:", err.message);
    return res.status(500).json({
      error: "Erro ao processar a pergunta. Tente novamente.",
    });
  }
}
