import axios from 'axios';
import { CandidateProfile, InterviewSession, InterviewReport } from '../types';

const API_BASE = 'http://localhost:8000';

export async function uploadResumeFile(file: File): Promise<CandidateProfile> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await axios.post<{ success: boolean; profile: CandidateProfile }>(
    `${API_BASE}/api/interview/upload-resume`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60000 }
  );
  return res.data.profile;
}

export async function startInterviewSession(
  profile: CandidateProfile,
  interview_type: string,
  target_role: string,
  difficulty: string,
  total_questions: number
): Promise<InterviewSession> {
  const res = await axios.post<{ success: boolean; session: InterviewSession }>(
    `${API_BASE}/api/interview/start`,
    { profile, interview_type, target_role, difficulty, total_questions },
    { timeout: 60000 }
  );
  return res.data.session;
}

export async function submitInterviewAnswer(
  session: InterviewSession,
  answer: string
): Promise<InterviewSession> {
  const res = await axios.post<{ success: boolean; session: InterviewSession }>(
    `${API_BASE}/api/interview/answer`,
    { session, answer },
    { timeout: 90000 }
  );
  return res.data.session;
}

export async function evaluateInterview(
  session: InterviewSession
): Promise<InterviewReport> {
  const res = await axios.post<{ success: boolean; report: InterviewReport }>(
    `${API_BASE}/api/interview/evaluate`,
    { session },
    { timeout: 90000 }
  );
  return res.data.report;
}
