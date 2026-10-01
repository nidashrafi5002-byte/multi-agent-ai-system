export type PipelineId = 'auto' | 'research' | 'stock' | 'code' | 'job' | 'flight' | 'image' | 'general' | 'interview';

export interface ExecutionStep {
  step: string;
  duration_ms: number;
}

export interface ChatResponse {
  domain: string;
  output: string;
  execution_log: ExecutionStep[];
  image_url?: string;
  enhanced_prompt?: string;
  stock_chart?: string;
  map_html?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  domain?: string;
  executionLog?: ExecutionStep[];
  imageUrl?: string;
  enhancedPrompt?: string;
  stockChart?: string;
  mapHtml?: string;
  createdAt: string;
}

export interface FlightRecord {
  flightNumber: string;
  origin: string;
  destination: string;
  aircraft: string;
  status: 'Boarding' | 'Delayed' | 'En Route' | 'Scheduled';
  lastUpdated: string;
  altitude: number;
  speed: number;
  latitude: number;
  longitude: number;
  path: [number, number][];
}

export interface AgentRecord {
  id: PipelineId;
  name: string;
  description: string;
  engine: string;
  accuracy: string;
  latency: string;
  active: boolean;
}

// ── Interview Feature Types ───────────────────────────────────────────────

export interface CandidateProject {
  title: string;
  technologies: string[];
  description: string;
  key_claims: string[];
}

export interface CandidateProfile {
  candidate_name: string;
  education: Array<{ degree: string; institution: string; year: string; gpa?: string }>;
  skills: string[];
  programming_languages: string[];
  frameworks_and_tools: string[];
  projects: CandidateProject[];
  experience: Array<{ role: string; company: string; duration: string; responsibilities: string[] }>;
  certifications: string[];
  achievements: string[];
  _raw_text?: string;
}

export interface RubricItem {
  score: number;
  justification: string;
}

export interface InterviewReport {
  executive_summary: string;
  overall_recommendation: string;
  rubric_scores: {
    technical_knowledge: RubricItem;
    project_understanding: RubricItem;
    communication_clarity: RubricItem;
    problem_solving: RubricItem;
  };
  strengths: string[];
  weak_areas: string[];
  claim_verifications: Array<{
    claim: string;
    finding: string;
    recommendation: string;
  }>;
  topics_to_revise: string[];
  next_steps: string[];
  questions_answered_well?: string[];
  questions_struggled?: string[];
}

export interface InterviewTurn {
  question: string;
  candidate_answer: string;
}

export interface InterviewSession {
  profile: CandidateProfile;
  interview_type: string;
  target_role: string;
  difficulty: string;
  total_questions: number;
  plan: Array<{ step: number; focus_area: string; inquiry_goal: string }>;
  history: InterviewTurn[];
  current_question: string;
  current_question_index: number;
  is_completed: boolean;
  last_assessment?: string;
  last_action?: 'PROBE' | 'CLARIFY' | 'CHALLENGE' | 'ADVANCE' | null;
  follow_ups_on_topic?: number;
  report?: InterviewReport;
}

export type InterviewStage = 'upload' | 'config' | 'interview' | 'report';

export interface InterviewConfig {
  targetRole: string;
  interviewType: string;
  difficulty: string;
  questionCount: number;
}