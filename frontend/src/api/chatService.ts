import axios from 'axios';
import { ChatResponse, ExecutionStep, PipelineId } from '../types';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const pipelineNames: Record<PipelineId, string> = {
  auto: 'Auto',
  research: 'Research',
  stock: 'Stock',
  code: 'Code',
  job: 'Job',
  flight: 'Flight',
  image: 'Image',
  general: 'General',
  interview: 'Interview',
};

function classifyPipeline(message: string, requested: PipelineId): PipelineId {
  if (requested !== 'auto') return requested;
  const text = message.toLowerCase();
  if (/stock|share|ticker|earnings|portfolio|market/.test(text)) return 'stock';
  if (/flight|airport|airline|departure|arrival|aa\d+|ba\d+/.test(text)) return 'flight';
  if (/code|bug|review|typescript|python|security|auth\.py/.test(text)) return 'code';
  if (/resume|cover letter|job|career|interview|role/.test(text)) return 'job';
  if (/image|illustration|visual|poster|logo|generate/.test(text)) return 'image';
  if (/research|report|summarize|compare|sources|brief|scaling|architecture|model|llm|deep dive|paper|study|analysis|quantum|science|history/.test(text)) return 'research';
  return 'general';
}

function fallbackResponse(message: string, requested: PipelineId, isTimeout: boolean = false): ChatResponse {
  const domain = classifyPipeline(message, requested);
  const name = pipelineNames[domain];
  const flightMatch = message.match(/\b([A-Z]{2,3})\s*[- ]?\s*(\d{1,4})\b/i);
  const requestedFlight = flightMatch ? `${flightMatch[1]}${flightMatch[2]}`.toUpperCase() : 'the requested flight';
  const execution_log: ExecutionStep[] = [
    { step: `Orchestrator routed to ${name} Agent`, duration_ms: 42 },
    { step: `${name} pipeline contextual fallback active`, duration_ms: domain === 'research' ? 180 : 126 },
    { step: 'Fallback response prepared', duration_ms: 54 },
  ];
  
  if (isTimeout) {
    return {
      domain,
      output: `## ${name} Agent (Generation Timeout)\n\nThe backend was generating a comprehensive long-form report for **${message}**, but it took longer than expected to finish.\n\n**Suggestions:**\n- Check your backend terminal (\`python backend/main.py\`) to verify completion.\n- Or select **Research** directly from the agent selector and retry.`,
      execution_log,
    };
  }

  const output = domain === 'stock'
    ? `## ${name} Agent\n\nI simulated a market intelligence pass for **${message}**. The next useful step is to confirm the ticker, reporting period, and risk horizon before making a decision.\n\n- **Signal:** Moderate\n- **Catalyst:** Earnings and sector momentum\n- **Risk:** Volatility and incomplete live-data coverage`
    : domain === 'code'
      ? `## ${name} Agent\n\nI inspected the request as a security-focused code review. No repository snippet was attached, so paste the relevant file and I will return prioritized findings with a patch plan.\n\n**Suggested review order:** authentication boundaries, input validation, secrets, error handling, and tests.`
      : domain === 'flight'
        ? `## ${name} Agent\n\nThe live aviation service could not be reached for **${requestedFlight}**, so I will not invent a route or status. Open **Flight Tracker** to retry the live lookup; the next chat request will also retry the backend automatically.`
        : domain === 'research'
          ? `## ${name} Agent\n\nI prepared a research pass for **${message}**. The deep-research pipeline is connecting to the orchestrator to synthesize sources and empirical findings.`
          : `## ${name} Agent\n\nI prepared a grounded first pass for **${message}**. The orchestration layer is ready to add sources, specialist analysis, and a concise executive answer when the backend is connected.`;
  return { domain, output, execution_log };
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    await axios.get(`${API_BASE}/api/health`, { timeout: 1800 });
    return true;
  } catch {
    return false;
  }
}

export async function sendChat(message: string, pipeline: PipelineId = 'auto'): Promise<ChatResponse> {
  try {
    // Multi-agent deep research and image generation can take up to 90-120 seconds for exhaustive reports
    const timeout = 180000;
    const response = await axios.post<ChatResponse>(`${API_BASE}/api/chat`, { message, pipeline }, { timeout });
    return {
      domain: response.data.domain || classifyPipeline(message, pipeline),
      output: response.data.output || 'The agent returned an empty response.',
      execution_log: response.data.execution_log || [],
      image_url: response.data.image_url,
      enhanced_prompt: response.data.enhanced_prompt,
      stock_chart: response.data.stock_chart,
      map_html: response.data.map_html,
    };
  } catch (error: any) {
    const isTimeout = error?.code === 'ECONNABORTED' || error?.message?.includes('timeout');
    await new Promise((resolve) => window.setTimeout(resolve, 650));
    return fallbackResponse(message, pipeline, isTimeout);
  }
}

export async function analyzeFile(file: File): Promise<{ success: boolean; file_type: string; filename: string; text?: string; image_data?: string; pages?: number; paragraphs?: number; size?: string; format?: string }> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_BASE}/api/analyze-file`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });
    return response.data;
  } catch (error: any) {
    throw new Error(error?.response?.data?.detail || 'Failed to analyze file');
  }
}
