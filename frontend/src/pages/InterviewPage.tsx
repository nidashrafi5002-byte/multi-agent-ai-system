import React, { useEffect, useState } from 'react';
import { checkBackendHealth } from '../api/chatService';
import {
  Award,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileText,
  MessageSquare,
  Play,
  RotateCcw,
  Send,
  Sparkles,
  Upload,
  UserCheck,
  AlertTriangle
} from 'lucide-react';
import { uploadResumeFile, startInterviewSession, submitInterviewAnswer } from '../api/interviewService';
import { CandidateProfile, InterviewSession } from '../types';

export function InterviewPage() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [answerInput, setAnswerInput] = useState('');
  const [showResumeContext, setShowResumeContext] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState(true);

  useEffect(() => {
    checkBackendHealth().then(setBackendOnline);
  }, []);

  // Configuration form state
  const [interviewType, setInterviewType] = useState('Project Defense');
  const [targetRole, setTargetRole] = useState('AI Engineer');
  const [difficulty, setDifficulty] = useState('Mid-Level');
  const [questionCount, setQuestionCount] = useState(5);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const parsedProfile = await uploadResumeFile(file);
      setProfile(parsedProfile);
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.detail || 'Failed to parse resume. Please ensure it is a valid PDF or DOCX file.');
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    if (!profile) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const newSession = await startInterviewSession(profile, interviewType, targetRole, difficulty, questionCount);
      setSession(newSession);
    } catch (err: any) {
      setErrorMessage('Failed to start interview. Check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!session || !answerInput.trim() || loading) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const updated = await submitInterviewAnswer(session, answerInput);
      setSession(updated);
      setAnswerInput('');
    } catch (err: any) {
      setErrorMessage('Error submitting answer. Please retry.');
    } finally {
      setLoading(false);
    }
  };

  const resetAll = () => {
    setProfile(null);
    setSession(null);
    setAnswerInput('');
    setErrorMessage(null);
  };

  return (
    <div className="page-content" style={{ maxWidth: '1000px', margin: '0 auto', padding: '30px 24px' }}>
      <header className="page-header" style={{ marginBottom: '25px' }}>
        <div>
          <span className="eyebrow-label">Adaptive Simulation</span>
          <h1>🎙️ AI Interviewer & Project Defense</h1>
          <p>Realistic, adaptive technical interviews grounded directly in your resume.</p>
        </div>
      </header>

      {errorMessage && (
        <div style={{ background: 'rgba(239,83,80,0.15)', border: '1px solid rgba(239,83,80,0.4)', borderRadius: '10px', padding: '12px 16px', color: '#ff8a80', marginBottom: '20px' }}>
          {errorMessage}
        </div>
      )}

      {/* STAGE 1: Upload Resume */}
      {!profile && (
        <div className="feature-card" style={{ padding: '40px', textAlign: 'center' }}>
          <div className="empty-icon" style={{ margin: '0 auto 15px' }}><Upload size={28} /></div>
          <h2>Upload Your Resume to Begin</h2>
          <p style={{ color: '#888', maxWidth: '480px', margin: '8px auto 24px' }}>
            MAIA analyzes your skills, projects, and technologies to generate tailored technical inquiries and project-defense probes.
          </p>
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: '#3a6fff', color: '#fff', padding: '10px 24px', borderRadius: '10px', cursor: 'pointer', fontWeight: 600 }}>
            <FileText size={18} /> Choose Resume (PDF or DOCX)
            <input type="file" accept=".pdf,.docx,.txt" onChange={handleFileUpload} style={{ display: 'none' }} />
          </label>
          {loading && <p style={{ marginTop: '16px', color: '#64b5f6' }}>⚡ Parsing resume & extracting candidate profile...</p>}
          {!backendOnline && (
            <p style={{ marginTop: '16px', color: '#ffb74d', fontSize: '13px' }}>
              Backend is offline. Start it with <code style={{ color: '#ccc' }}>python backend\main.py</code> or run <code style={{ color: '#ccc' }}>start_all.bat</code>.
            </p>
          )}
        </div>
      )}

      {/* STAGE 2: Configure Interview */}
      {profile && !session && (
        <div>
          <div className="feature-card" style={{ padding: '24px', marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <UserCheck size={20} color="#64b5f6" /> {profile.candidate_name || 'Candidate Profile'}
              </h3>
              <button className="text-button" onClick={resetAll}><RotateCcw size={14} /> Re-upload</button>
            </div>
            <div style={{ fontSize: '13px', color: '#aaa', lineHeight: 1.6 }}>
              {profile.education?.length > 0 && (
                <div><strong>Education:</strong> {profile.education.map(e => `${e.degree} — ${e.institution}`).join(' · ')}</div>
              )}
              <div><strong>Skills:</strong> {profile.skills.slice(0, 12).join(', ') || 'N/A'}</div>
              <div><strong>Languages:</strong> {profile.programming_languages.join(', ') || 'N/A'}</div>
              <div><strong>Tools & Frameworks:</strong> {profile.frameworks_and_tools.slice(0, 10).join(', ') || 'N/A'}</div>
              <div><strong>Projects:</strong> {profile.projects.map(p => p.title).join(' · ') || 'None listed'}</div>
              {profile.experience?.length > 0 && (
                <div><strong>Experience:</strong> {profile.experience.map(e => `${e.role} @ ${e.company}`).join(' · ')}</div>
              )}
            </div>
            <p style={{ fontSize: '11px', color: '#666', marginTop: '12px', marginBottom: 0 }}>
              Profile extracted from your resume only — interview questions will reference these claims.
            </p>
          </div>

          <div className="feature-card" style={{ padding: '28px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '20px' }}>Configure Your Interview Session</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px', marginBottom: '24px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#888', marginBottom: '6px' }}>Interview Type</label>
                <select value={interviewType} onChange={e => setInterviewType(e.target.value)} style={{ width: '100%', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#eee', borderRadius: '8px' }}>
                  <option value="Project Defense">Project Defense</option>
                  <option value="Technical Interview">Technical Interview</option>
                  <option value="HR Interview">HR Interview</option>
                  <option value="DSA/Coding Interview">DSA/Coding Interview</option>
                  <option value="Mixed Interview">Mixed Interview</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#888', marginBottom: '6px' }}>Target Role</label>
                <input value={targetRole} onChange={e => setTargetRole(e.target.value)} placeholder="e.g. AI Engineer, Backend Lead" style={{ width: '100%', padding: '9px 12px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#eee', borderRadius: '8px' }} />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#888', marginBottom: '6px' }}>Seniority Level</label>
                <select value={difficulty} onChange={e => setDifficulty(e.target.value)} style={{ width: '100%', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#eee', borderRadius: '8px' }}>
                  <option value="Entry / Junior">Entry / Junior</option>
                  <option value="Mid-Level">Mid-Level</option>
                  <option value="Senior / Lead">Senior / Lead</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#888', marginBottom: '6px' }}>Question Count</label>
                <select value={questionCount} onChange={e => setQuestionCount(Number(e.target.value))} style={{ width: '100%', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#eee', borderRadius: '8px' }}>
                  <option value={3}>3 Questions (Quick)</option>
                  <option value={5}>5 Questions (Standard)</option>
                  <option value={8}>8 Questions (In-Depth)</option>
                </select>
              </div>
            </div>

            <button onClick={handleStart} disabled={loading} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: '#3a6fff', color: '#fff', padding: '12px 28px', border: 0, borderRadius: '10px', fontWeight: 600, cursor: 'pointer' }}>
              <Play size={18} /> {loading ? 'Planning Interview...' : 'Start Adaptive Interview'}
            </button>
          </div>
        </div>
      )}

      {/* STAGE 3: Active Adaptive Interview */}
      {session && !session.is_completed && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', fontSize: '13px', color: '#888' }}>
            <span>
              {session.last_action && session.last_action !== 'ADVANCE' && (
                <span style={{ color: '#ffb74d', marginRight: '6px' }}>Follow-up ({session.last_action.toLowerCase()}) ·</span>
              )}
              Topic {Math.min(session.current_question_index + 1, session.total_questions)} of {session.total_questions} · <strong>{session.difficulty} {session.interview_type}</strong>
            </span>
            <button className="text-button" onClick={() => setShowResumeContext(!showResumeContext)}>
              {showResumeContext ? <ChevronUp size={14} /> : <ChevronDown size={14} />} Resume Reference
            </button>
          </div>

          {showResumeContext && (
            <div className="feature-card" style={{ padding: '14px 18px', marginBottom: '18px', fontSize: '12px', color: '#bbb' }}>
              <strong>Your Listed Projects:</strong> {profile?.projects.map(p => p.title).join(' · ')}
            </div>
          )}

          {/* Previous Conversation Turns */}
          {session.history.map((turn, i) => (
            <div key={i} style={{ marginBottom: '16px', padding: '14px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', borderLeft: '3px solid #3a6fff' }}>
              <div style={{ color: '#64b5f6', fontWeight: 600, fontSize: '13px', marginBottom: '4px' }}>🤖 Interviewer:</div>
              <div style={{ color: '#ddd', fontSize: '14px', marginBottom: '8px' }}>{turn.question}</div>
              <div style={{ color: '#888', fontWeight: 600, fontSize: '13px', marginBottom: '4px' }}>🧑 Your Answer:</div>
              <div style={{ color: '#bbb', fontSize: '13px' }}>{turn.candidate_answer}</div>
            </div>
          ))}

          {session.last_assessment && (
            <div style={{ fontSize: '12px', color: '#888', marginBottom: '12px', fontStyle: 'italic' }}>
              <Sparkles size={12} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
              Interviewer note: {session.last_assessment}
            </div>
          )}

          {/* Current Question Focus Card */}
          <div className="feature-card" style={{ padding: '24px', border: '1px solid rgba(58,111,255,0.3)', background: 'rgba(58,111,255,0.06)', marginBottom: '20px' }}>
            <div style={{ color: '#64b5f6', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700, marginBottom: '8px' }}>
              AI Interviewer
            </div>
            <div style={{ fontSize: '16px', color: '#f1f1f1', fontWeight: 500, lineHeight: 1.5 }}>
              {session.current_question}
            </div>
          </div>

          {/* Answer Text Area */}
          <div style={{ marginBottom: '16px' }}>
            <textarea
              rows={5}
              value={answerInput}
              onChange={e => setAnswerInput(e.target.value)}
              placeholder="Explain your approach, architectural rationale, and implementation details..."
              style={{ width: '100%', padding: '14px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#eee', borderRadius: '12px', fontSize: '14px', resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={handleSubmitAnswer}
              disabled={loading || !answerInput.trim()}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: '#3a6fff', color: '#fff', padding: '11px 24px', border: 0, borderRadius: '9px', fontWeight: 600, cursor: 'pointer', opacity: loading || !answerInput.trim() ? 0.4 : 1 }}
            >
              <Send size={16} /> {loading
                ? (session.current_question_index + 1 >= session.total_questions ? 'Generating report...' : 'Adapting question...')
                : 'Submit Answer'}
            </button>
          </div>
        </div>
      )}

      {/* STAGE 4: Final Evaluation Report */}
      {session && session.is_completed && session.report && (
        <div>
          <div className="feature-card" style={{ padding: '28px', marginBottom: '22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ margin: 0 }}>🎉 Interview Evaluation Report</h2>
              <span className="metric-badge success">{session.report.overall_recommendation}</span>
            </div>
            <p style={{ color: '#bbb', fontSize: '14px', lineHeight: 1.6 }}>{session.report.executive_summary}</p>
          </div>

          {/* Rubric Score Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '22px' }}>
            {Object.entries(session.report.rubric_scores).map(([key, val]) => (
              <div key={key} className="feature-card" style={{ padding: '18px' }}>
                <span style={{ fontSize: '11px', color: '#888', textTransform: 'capitalize' }}>{key.replace('_', ' ')}</span>
                <div style={{ fontSize: '24px', fontWeight: 700, color: '#64b5f6', margin: '6px 0' }}>{val.score}/100</div>
                <div style={{ fontSize: '11px', color: '#aaa', lineHeight: 1.4 }}>{val.justification}</div>
              </div>
            ))}
          </div>

          {/* Strengths & Weak Areas */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '22px' }}>
            <div className="feature-card" style={{ padding: '20px' }}>
              <h4 style={{ margin: '0 0 12px', color: '#81c784', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={16} /> Demonstrated Strengths
              </h4>
              <ul style={{ margin: 0, paddingLeft: '18px', color: '#bbb', fontSize: '13px' }}>
                {session.report.strengths.map((s, i) => <li key={i} style={{ marginBottom: '6px' }}>{s}</li>)}
              </ul>
            </div>

            <div className="feature-card" style={{ padding: '20px' }}>
              <h4 style={{ margin: '0 0 12px', color: '#ffb74d', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={16} /> Key Growth Areas
              </h4>
              <ul style={{ margin: 0, paddingLeft: '18px', color: '#bbb', fontSize: '13px' }}>
                {session.report.weak_areas.map((w, i) => <li key={i} style={{ marginBottom: '6px' }}>{w}</li>)}
              </ul>
            </div>
          </div>

          {(session.report.questions_answered_well?.length || session.report.questions_struggled?.length) ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '22px' }}>
              {session.report.questions_answered_well && session.report.questions_answered_well.length > 0 && (
                <div className="feature-card" style={{ padding: '20px' }}>
                  <h4 style={{ margin: '0 0 12px', color: '#81c784', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <MessageSquare size={16} /> Answered Well
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: '18px', color: '#bbb', fontSize: '13px' }}>
                    {session.report.questions_answered_well.map((q, i) => <li key={i} style={{ marginBottom: '6px' }}>{q}</li>)}
                  </ul>
                </div>
              )}
              {session.report.questions_struggled && session.report.questions_struggled.length > 0 && (
                <div className="feature-card" style={{ padding: '20px' }}>
                  <h4 style={{ margin: '0 0 12px', color: '#ffb74d', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <MessageSquare size={16} /> Needs Improvement
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: '18px', color: '#bbb', fontSize: '13px' }}>
                    {session.report.questions_struggled.map((q, i) => <li key={i} style={{ marginBottom: '6px' }}>{q}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ) : null}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '22px' }}>
            <div className="feature-card" style={{ padding: '20px' }}>
              <h4 style={{ margin: '0 0 12px', color: '#64b5f6', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Award size={16} /> Topics to Revise
              </h4>
              <ul style={{ margin: 0, paddingLeft: '18px', color: '#bbb', fontSize: '13px' }}>
                {(session.report.topics_to_revise || []).map((t, i) => <li key={i} style={{ marginBottom: '6px' }}>{t}</li>)}
              </ul>
            </div>
            <div className="feature-card" style={{ padding: '20px' }}>
              <h4 style={{ margin: '0 0 12px', color: '#64b5f6' }}>Suggested Next Steps</h4>
              <ul style={{ margin: 0, paddingLeft: '18px', color: '#bbb', fontSize: '13px' }}>
                {(session.report.next_steps || []).map((t, i) => <li key={i} style={{ marginBottom: '6px' }}>{t}</li>)}
              </ul>
            </div>
          </div>

          {/* Resume Claim Verification */}
          {session.report.claim_verifications && session.report.claim_verifications.length > 0 && (
            <div className="feature-card" style={{ padding: '22px', borderLeft: '4px solid #ffb74d', marginBottom: '22px' }}>
              <h4 style={{ margin: '0 0 10px', color: '#ffb74d' }}>🔍 Resume Claim Verification</h4>
              {session.report.claim_verifications.map((c, i) => (
                <div key={i} style={{ fontSize: '13px', color: '#bbb', marginBottom: '10px' }}>
                  <div><strong>Claim:</strong> {c.claim}</div>
                  <div><strong>Observed:</strong> {c.finding}</div>
                  <div style={{ color: '#64b5f6' }}>💡 <em>{c.recommendation}</em></div>
                </div>
              ))}
            </div>
          )}

          <button onClick={resetAll} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: '#3a6fff', color: '#fff', padding: '12px 24px', border: 0, borderRadius: '9px', fontWeight: 600, cursor: 'pointer' }}>
            <RotateCcw size={16} /> Start Another Interview
          </button>
        </div>
      )}
    </div>
  );
}