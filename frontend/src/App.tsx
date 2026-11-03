import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent, ReactNode, RefObject } from 'react'
import { AlertCircle, ArrowUpRight, BrainCircuit, BriefcaseBusiness, Check, CheckCircle2, ChevronRight, CirclePlus, FileText, GitCompareArrows, LayoutDashboard, LoaderCircle, Search, Sparkles, Users, X, Zap } from 'lucide-react'

const API = import.meta.env.VITE_API_URL ?? `${window.location.protocol}//${window.location.hostname}:8001/api/v1`
type PipelineStage = 'new' | 'reviewing' | 'shortlisted' | 'interview' | 'rejected'
type Candidate = { id: number; full_name: string; email: string; phone?: string | null; years_experience?: number | null; skills: string[]; education?: string[]; projects?: string[]; certifications?: string[]; work_history?: string[]; pipeline_stage: PipelineStage; recruiter_notes?: string | null }
type Job = { id: number; title?: string | null; description?: string | null; min_experience?: number | null; skills: string[]; requirements: string[] }
type ScoreComponent = { signal: string; weight: number; raw_score?: number | null; contribution: number; description: string }
type Match = { candidate_id: number; candidate_name: string; match_score: number; matched_skills: string[]; candidate_experience?: number | null; hiring_recommendation?: string; candidate_summary?: string; strengths?: string[]; weaknesses?: string[]; recommendation_reason?: string; score_breakdown?: ScoreComponent[]; fairness_note?: string }
type CandidateRoleMatch = { job_id: number; job_title?: string | null; match_score: number; matched_skills: string[]; missing_skills: string[]; fit_explanation: string }
type RoleDecisionStatus = 'shortlisted' | 'interview' | 'rejected'
type RoleDecision = { candidate_id: number; job_id: number; decision: RoleDecisionStatus; notes?: string | null; updated_at: string }
type AISearchResult = Candidate & { relevance_score: number; matched_terms: string[]; search_explanation: string }
type InterpretedFilters = { min_experience: number | null; max_experience: number | null; required_skills: string[]; any_skills: string[]; exclusive_skills: string[]; excluded_skills: string[]; required_terms: string[]; skill_operator: 'AND' | 'OR' | 'XOR'; has_constraints: boolean; parser: string; sql_preview?: string }
type AIBrief = { answer: string; retrieval_method: string; grounding_note: string; semantic_retrieval_active: boolean; generation_mode: string; retrieval_latency_ms: number; index_sync: { indexed: number; unchanged: number; removed: number; total: number }; interpreted_filters: InterpretedFilters; sources: AISearchResult[] }
type AIRuntime = { embedding_model: string; vector_store: string; ollama_configured: boolean; ollama_model: string; semantic_retrieval_ready: boolean; generation_ready: boolean; last_error?: string | null }
type View = 'overview' | 'candidates' | 'roles' | 'ai'
type ModalKind = 'candidate' | 'job' | 'resume' | 'brief'

const initials = (name: string) => name.split(' ').map((item) => item[0]).join('').slice(0, 2).toUpperCase()
const toList = (text: string) => text.split(',').map((item) => item.trim()).filter(Boolean)
const pipelineStages: Array<{ value: PipelineStage; label: string }> = [{ value: 'new', label: 'New' }, { value: 'reviewing', label: 'Reviewing' }, { value: 'shortlisted', label: 'Shortlisted' }, { value: 'interview', label: 'Interview' }, { value: 'rejected', label: 'Rejected' }]
const stageLabel = (stage: PipelineStage) => pipelineStages.find((item) => item.value === stage)?.label ?? stage
const decisionLabel = (decision: RoleDecisionStatus) => decision === 'shortlisted' ? 'Shortlisted' : decision === 'interview' ? 'Interview' : 'Rejected'
const queryPlanLabel = (filters: InterpretedFilters) => {
  const parts: string[] = []
  if (filters.min_experience !== null) parts.push(`${filters.min_experience}+ years`)
  if (filters.max_experience !== null) parts.push(`up to ${filters.max_experience} years`)
  if (filters.exclusive_skills.length) parts.push(`exactly one of ${filters.exclusive_skills.join(' / ')}`)
  if (filters.required_skills.length) parts.push(`all of ${filters.required_skills.join(' + ')}`)
  if (filters.any_skills.length) parts.push(`any of ${filters.any_skills.join(' / ')}`)
  if (filters.excluded_skills.length) parts.push(`excluding ${filters.excluded_skills.join(' / ')}`)
  if (filters.required_terms.length) parts.push(`profile terms: ${filters.required_terms.join(' + ')}`)
  return parts.join(' · ')
}
const readableQueryPlan = (filters: InterpretedFilters) => JSON.stringify({
  min_experience: filters.min_experience,
  max_experience: filters.max_experience,
  skills: filters.exclusive_skills.length ? filters.exclusive_skills : filters.required_skills.length ? filters.required_skills : filters.any_skills,
  skill_operator: filters.skill_operator,
  excluded_skills: filters.excluded_skills,
  required_terms: filters.required_terms,
  semantic_query: filters.has_constraints ? 'Original recruiter query, used only to rerank valid results' : 'Original recruiter query',
}, null, 2)

async function responseError(response: Response) {
  const fallback = `Request failed with status ${response.status}.`
  try {
    const payload = await response.json()
    return payload.detail ?? payload.message ?? fallback
  } catch {
    return fallback
  }
}

export default function App() {
  const [view, setView] = useState<View>('overview')
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [job, setJob] = useState<Job | null>(null)
  const [matches, setMatches] = useState<Match[]>([])
  const [roleDecisions, setRoleDecisions] = useState<RoleDecision[]>([])
  const [compareCandidateIds, setCompareCandidateIds] = useState<number[]>([])
  const [comparisonOpen, setComparisonOpen] = useState(false)
  const [aiQuery, setAIQuery] = useState('')
  const [aiBrief, setAIBrief] = useState<AIBrief | null>(null)
  const [aiRuntime, setAIRuntime] = useState<AIRuntime | null>(null)
  const [aiLoading, setAILoading] = useState(false)
  const [search, setSearch] = useState('')
  const [stageFilter, setStageFilter] = useState<PipelineStage | 'all'>('all')
  const [modal, setModal] = useState<ModalKind | null>(null)
  const [insight, setInsight] = useState<Match | null>(null)
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [candidateRoles, setCandidateRoles] = useState<CandidateRoleMatch[]>([])
  const [candidateRolesLoading, setCandidateRolesLoading] = useState(false)
  const [profileMenuOpen, setProfileMenuOpen] = useState(false)
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const searchInput = useRef<HTMLInputElement>(null)

  const loadMatches = async (id: number) => {
    const response = await fetch(`${API}/jobs/${id}/candidates`)
    setMatches(response.ok ? await response.json() : [])
  }

  const loadDecisions = async (id: number) => {
    const response = await fetch(`${API}/jobs/${id}/decisions`)
    setRoleDecisions(response.ok ? await response.json() : [])
  }

  const load = async () => {
    setLoading(true)
    try {
      const [peopleResponse, rolesResponse] = await Promise.all([fetch(`${API}/candidates/`), fetch(`${API}/jobs/`)])
      if (!peopleResponse.ok || !rolesResponse.ok) throw new Error('API returned an error')
      const people = await peopleResponse.json()
      const roles = await rolesResponse.json()
      setCandidates(people)
      setJobs(roles)
      const current = job ?? roles[0]
      if (current) {
        setJob(current)
        await Promise.all([loadMatches(current.id), loadDecisions(current.id)])
      }
    } catch {
      setStatus(`API offline at ${API}. Start FastAPI on port 8000, then retry.`)
    }
    setLoading(false)
  }

  useEffect(() => { void load() }, [])

  const chooseJob = async (next: Job) => {
    setJob(next)
    setInsight(null)
    setCompareCandidateIds([])
    await Promise.all([loadMatches(next.id), loadDecisions(next.id)])
  }

  const goHome = () => {
    setView('overview')
    setInsight(null)
    setSelectedCandidate(null)
    setProfileMenuOpen(false)
  }

  const openSearch = () => {
    setView('candidates')
    window.setTimeout(() => searchInput.current?.focus(), 0)
  }

  const openCandidate = async (candidate: Candidate) => {
    setSelectedCandidate(candidate)
    setCandidateRoles([])
    setCandidateRolesLoading(true)
    try {
      const response = await fetch(`${API}/candidates/${candidate.id}/jobs`)
      if (!response.ok) throw new Error(await responseError(response))
      setCandidateRoles(await response.json())
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Could not load candidate recommendations.')
    } finally {
      setCandidateRolesLoading(false)
    }
  }

  const openRoleFromCandidate = async (match: CandidateRoleMatch) => {
    const next = jobs.find((item) => item.id === match.job_id)
    if (!next) return
    setSelectedCandidate(null)
    setView('roles')
    await chooseJob(next)
  }

  const saveCandidateWorkflow = async (candidate: Candidate, pipelineStage: PipelineStage, recruiterNotes: string) => {
    try {
      const response = await fetch(`${API}/candidates/${candidate.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pipeline_stage: pipelineStage, recruiter_notes: recruiterNotes || null }),
      })
      if (!response.ok) throw new Error(await responseError(response))
      const updated = await response.json() as Candidate
      setCandidates((current) => current.map((item) => item.id === updated.id ? updated : item))
      setSelectedCandidate(updated)
      setStatus(`${updated.full_name} moved to ${stageLabel(updated.pipeline_stage)}.`)
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Could not save the candidate workflow.')
    }
  }

  const saveRoleDecision = async (candidateId: number, decision: RoleDecisionStatus, notes: string) => {
    if (!job) return
    try {
      const response = await fetch(`${API}/jobs/${job.id}/candidates/${candidateId}/decision`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, notes: notes || null }),
      })
      if (!response.ok) throw new Error(await responseError(response))
      const saved = await response.json() as RoleDecision
      setRoleDecisions((current) => [...current.filter((item) => item.candidate_id !== saved.candidate_id), saved])
      const match = matches.find((item) => item.candidate_id === candidateId)
      setStatus(`${match?.candidate_name ?? 'Candidate'} marked ${decisionLabel(saved.decision).toLowerCase()} for this role.`)
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Could not save the role decision.')
    }
  }

  const toggleComparison = (candidateId: number) => {
    setCompareCandidateIds((current) => current.includes(candidateId) ? current.filter((id) => id !== candidateId) : current.length === 3 ? [...current.slice(1), candidateId] : [...current, candidateId])
  }

  const runAIRetrieval = async (generate = false) => {
    const query = aiQuery.trim()
    if (query.length < 2) {
      setStatus('Enter a more specific AI retrieval query.')
      return
    }
    setAILoading(true)
    try {
      const response = await fetch(`${API}/ai/recruiter-brief`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 5, generate }),
      })
      if (!response.ok) throw new Error(await responseError(response))
      setAIBrief(await response.json())
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'AI retrieval could not complete.')
    } finally {
      setAILoading(false)
    }
  }

  const refreshAIRuntime = async () => {
    try {
      void fetch(`${API}/ai/warmup`, { method: 'POST' })
      const response = await fetch(`${API}/ai/runtime-check`)
      if (response.ok) setAIRuntime(await response.json())
    } catch {
      setAIRuntime(null)
    }
  }

  const reindexCandidateKnowledgeBase = async () => {
    setAILoading(true)
    try {
      const response = await fetch(`${API}/ai/reindex`, { method: 'POST' })
      if (!response.ok) throw new Error(await responseError(response))
      const result = await response.json() as { indexed: number; model: string }
      setStatus(`AI knowledge base refreshed: ${result.indexed} candidate profiles indexed.`)
      await refreshAIRuntime()
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Could not refresh the AI knowledge base.')
    } finally {
      setAILoading(false)
    }
  }

  useEffect(() => { if (view === 'ai') void refreshAIRuntime() }, [view])

  const shortlisted = [...matches].sort((a, b) => b.match_score - a.match_score)
  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return candidates.filter((candidate) => `${candidate.full_name} ${candidate.email} ${candidate.skills.join(' ')}`.toLowerCase().includes(q) && (stageFilter === 'all' || candidate.pipeline_stage === stageFilter))
  }, [candidates, search, stageFilter])
  const average = matches.length ? Math.round(matches.reduce((sum, match) => sum + match.match_score, 0) / matches.length) : 0

  const save = async (event: FormEvent<HTMLFormElement>, kind: ModalKind) => {
    event.preventDefault()
    if (saving) return
    const form = new FormData(event.currentTarget)
    setSaving(true)
    try {
      const responses: Response[] = []
      if (kind === 'candidate') responses.push(await fetch(`${API}/candidates/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ full_name: form.get('name'), email: form.get('email'), years_experience: Number(form.get('experience')) || null, skills: toList(String(form.get('skills') || '')) }) }))
      if (kind === 'job') responses.push(await fetch(`${API}/jobs/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: form.get('title'), description: form.get('description'), min_experience: Number(form.get('experience')) || null, skills: toList(String(form.get('skills') || '')), requirements: toList(String(form.get('requirements') || '')) }) }))
      if (kind === 'resume') responses.push(await fetch(`${API}/resumes/extract`, { method: 'POST', body: form }))
      if (kind === 'brief') responses.push(await fetch(`${API}/jobs/extract`, { method: 'POST', body: form }))
      const failedResponse = responses.find((response) => !response.ok)
      if (failedResponse) throw new Error(await responseError(failedResponse))
      setModal(null)
      setStatus(kind === 'resume' || kind === 'brief' ? 'Document processed and added to your workspace.' : 'Workspace updated.')
      await load()
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'That action did not complete. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const openInsight = async (match: Match) => {
    if (!job) return
    const response = await fetch(`${API}/jobs/${job.id}/candidates/${match.candidate_id}/insights`)
    if (response.ok) setInsight(await response.json())
  }

  const noticeIsSuccess = status === 'Workspace updated.' || status.startsWith('Document processed')

  return <main className="app-shell">
    <aside className="sidebar">
      <button className="brand" onClick={goHome} title="TalentIQ overview"><span><Zap size={15} /></span>TalentIQ</button>
      <button className="workspace" onClick={goHome} title="Open TalentIQ workspace"><i>TI</i><div><b>TalentIQ</b><small>Hiring intelligence</small></div><ChevronRight size={15} /></button>
      <nav>
        <Nav icon={<LayoutDashboard size={17} />} label="Overview" active={view === 'overview'} onClick={() => setView('overview')} />
        <Nav icon={<Users size={17} />} label="Candidates" count={candidates.length} active={view === 'candidates'} onClick={() => setView('candidates')} />
        <Nav icon={<BriefcaseBusiness size={17} />} label="Open roles" count={jobs.length} active={view === 'roles'} onClick={() => setView('roles')} />
        <Nav icon={<BrainCircuit size={17} />} label="AI intelligence" active={view === 'ai'} onClick={() => setView('ai')} />
      </nav>
      <div className="side-footer">
        <div className="ai-note"><Sparkles size={15} /><p>AI-grounded hiring decisions, one view.</p></div>
        <div className="profile-wrap">
          <button className="profile" onClick={() => setProfileMenuOpen((open) => !open)} aria-expanded={profileMenuOpen}><i>LR</i><span><b>Lead recruiter</b><small>TalentIQ workspace</small></span><ChevronRight size={15} /></button>
          {profileMenuOpen && <div className="profile-menu"><b>Lead recruiter</b><small>Hiring intelligence workspace</small><button onClick={goHome}>Go to overview</button></div>}
        </div>
      </div>
    </aside>
    <section className="content">
      <header className="topbar">
        <div><p className="eyebrow">Talent intelligence workspace</p><h1>{view === 'overview' ? 'Hiring, made legible.' : view === 'candidates' ? 'Candidate directory' : view === 'roles' ? 'Open roles' : 'AI intelligence'}</h1></div>
        <div><button className="icon-button" title="Search candidates" onClick={openSearch}><Search size={18} /></button><button className="primary-button" onClick={() => setModal(view === 'roles' ? 'job' : 'candidate')}><CirclePlus size={17} />{view === 'roles' ? 'New role' : 'Add candidate'}</button></div>
      </header>
      {status && <div className={noticeIsSuccess ? 'notice success' : 'notice error'}>{noticeIsSuccess ? <Check size={16} /> : <AlertCircle size={16} />}{status}{status.startsWith('API offline') && <button className="retry-button" onClick={() => void load()}>Retry</button>}<button title="Dismiss" onClick={() => setStatus('')}><X size={16} /></button></div>}
      {loading ? <div className="loading"><LoaderCircle size={22} />Loading workspace</div> : view === 'overview' ? <Overview candidates={candidates} jobs={jobs} job={job} matches={shortlisted} average={average} chooseJob={chooseJob} openInsight={openInsight} setModal={setModal} /> : view === 'candidates' ? <Candidates people={filtered} allPeople={candidates} search={search} setSearch={setSearch} stageFilter={stageFilter} setStageFilter={setStageFilter} searchInput={searchInput} openUpload={() => setModal('resume')} openCandidate={openCandidate} /> : view === 'roles' ? <Roles jobs={jobs} job={job} matches={shortlisted} decisions={roleDecisions} compareCandidateIds={compareCandidateIds} chooseJob={chooseJob} openInsight={openInsight} openUpload={() => setModal('brief')} toggleComparison={toggleComparison} openComparison={() => setComparisonOpen(true)} /> : <AIWorkspace query={aiQuery} setQuery={setAIQuery} brief={aiBrief} runtime={aiRuntime} loading={aiLoading} run={runAIRetrieval} reindex={reindexCandidateKnowledgeBase} openCandidate={openCandidate} />}
    </section>
    {insight && <Insight match={insight} decision={roleDecisions.find((item) => item.candidate_id === insight.candidate_id)} close={() => setInsight(null)} saveDecision={saveRoleDecision} />}
    {selectedCandidate && <CandidateProfile candidate={selectedCandidate} matches={candidateRoles} loading={candidateRolesLoading} close={() => setSelectedCandidate(null)} openRole={openRoleFromCandidate} saveWorkflow={saveCandidateWorkflow} />}
    {comparisonOpen && <ComparisonPanel matches={matches.filter((match) => compareCandidateIds.includes(match.candidate_id))} candidates={candidates} decisions={roleDecisions} close={() => setComparisonOpen(false)} />}
    {modal && <Modal kind={modal} close={() => setModal(null)} save={save} saving={saving} />}
  </main>
}

function Nav({ icon, label, count, active, onClick }: { icon: ReactNode; label: string; count?: number; active: boolean; onClick: () => void }) { return <button className={active ? 'nav active' : 'nav'} onClick={onClick}>{icon}<span>{label}</span>{count !== undefined && <small>{count}</small>}</button> }
function Overview({ candidates, jobs, job, matches, average, chooseJob, openInsight, setModal }: { candidates: Candidate[]; jobs: Job[]; job: Job | null; matches: Match[]; average: number; chooseJob: (job: Job) => void; openInsight: (match: Match) => void; setModal: (value: 'resume' | 'brief') => void }) { return <div className="grid"><section className="pulse"><div><p className="label">AI hiring pulse</p><h2>Make the shortlist<br />feel obvious.</h2><p>Review AI-assisted signals from your active search.</p><button onClick={() => job && void chooseJob(job)}>Review AI matches <ArrowUpRight size={16} /></button></div><aside><span>AI TOP FIT</span><b>{matches[0] ? `${Math.round(matches[0].match_score)}%` : '0%'}</b><small>match confidence</small></aside></section><section className="metrics"><Metric label="Talent pool" value={candidates.length} text="qualified profiles" /><Metric label="Open roles" value={jobs.length} text="actively hiring" /><Metric label="AI fit score" value={`${average}%`} text="for selected role" /></section><section className="surface shortlist"><Header label="AI-ranked shortlist" title={job?.title ?? 'Shortlist'} extra={<select value={job?.id ?? ''} onChange={(event) => { const found = jobs.find((item) => item.id === Number(event.target.value)); if (found) void chooseJob(found) }}><option value="">Choose role</option>{jobs.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>} />{matches.length ? matches.slice(0, 4).map((match, index) => <button className="shortlist-row" key={match.candidate_id} onClick={() => void openInsight(match)}><em>0{index + 1}</em><Avatar name={match.candidate_name} index={index} /><span><b>{match.candidate_name}</b><small>{match.candidate_experience ?? 0} years experience</small></span><i>{Math.round(match.match_score)}% fit</i><ChevronRight size={17} /></button>) : <Empty text="Add candidates and a role to start AI-assisted ranking." />}</section><section className="surface intake"><Header label="AI data intake" title="Keep the pipeline moving" /><button onClick={() => setModal('resume')}><span><Users size={18} /></span><div><b>Import a resume</b><small>PDF or DOCX</small></div><ChevronRight size={17} /></button><button onClick={() => setModal('brief')}><span className="amber"><FileText size={18} /></span><div><b>Import a job brief</b><small>Build a role from a document</small></div><ChevronRight size={17} /></button></section></div> }
function Metric({ label, value, text }: { label: string; value: string | number; text: string }) { return <div><p>{label}</p><b>{value}</b><small>{text}</small></div> }
function Header({ label, title, extra }: { label: string; title: string; extra?: ReactNode }) { return <header className="section-header"><div><p className="label">{label}</p><h3>{title}</h3></div>{extra}</header> }
function Avatar({ name, index = 0 }: { name: string; index?: number }) { return <i className={`avatar avatar-${index % 4}`}>{initials(name)}</i> }
function Candidates({ people, allPeople, search, setSearch, stageFilter, setStageFilter, searchInput, openUpload, openCandidate }: { people: Candidate[]; allPeople: Candidate[]; search: string; setSearch: (value: string) => void; stageFilter: PipelineStage | 'all'; setStageFilter: (value: PipelineStage | 'all') => void; searchInput: RefObject<HTMLInputElement | null>; openUpload: () => void; openCandidate: (candidate: Candidate) => Promise<void> }) { return <div className="directory"><section className="pipeline-strip">{pipelineStages.slice(0, 4).map((stage) => <button key={stage.value} className={stageFilter === stage.value ? 'active' : ''} onClick={() => setStageFilter(stageFilter === stage.value ? 'all' : stage.value)}><span>{stage.label}</span><b>{allPeople.filter((candidate) => candidate.pipeline_stage === stage.value).length}</b></button>)}<button className={stageFilter === 'rejected' ? 'active muted' : 'muted'} onClick={() => setStageFilter(stageFilter === 'rejected' ? 'all' : 'rejected')}><span>Rejected</span><b>{allPeople.filter((candidate) => candidate.pipeline_stage === 'rejected').length}</b></button></section><div className="toolbar"><label><Search size={17} /><input ref={searchInput} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search skills, names, or email" /></label><div className="directory-actions"><select value={stageFilter} onChange={(event) => setStageFilter(event.target.value as PipelineStage | 'all')} aria-label="Filter candidates by pipeline stage"><option value="all">All stages</option>{pipelineStages.map((stage) => <option key={stage.value} value={stage.value}>{stage.label}</option>)}</select><button className="secondary-button" onClick={openUpload}><FileText size={16} />Import resume</button></div></div><section className="surface table"><header><span>Candidate</span><span>Expertise</span><span>Pipeline</span><span>Profile signal</span><span>Experience</span></header>{people.length ? people.map((person, index) => <button className="table-row" key={person.id} onClick={() => void openCandidate(person)} title={`Open ${person.full_name}'s profile`}><div><Avatar name={person.full_name} index={index} /><span><b>{person.full_name}</b><small>{person.email}</small></span></div><p>{person.skills.slice(0, 3).map((skill) => <i key={skill}>{skill}</i>)}</p><StageBadge stage={person.pipeline_stage} /><span className="profile-signal">{person.projects?.length || person.education?.length || person.certifications?.length ? 'Structured profile' : 'Basic profile'}</span><span>{person.years_experience ?? 0} yrs</span><ChevronRight size={17} /></button>) : <Empty text="No candidates match this search." />}</section></div> }
function AIWorkspace({ query, setQuery, brief, runtime, loading, run, reindex, openCandidate }: { query: string; setQuery: (value: string) => void; brief: AIBrief | null; runtime: AIRuntime | null; loading: boolean; run: (generate?: boolean) => Promise<void>; reindex: () => Promise<void>; openCandidate: (candidate: Candidate) => Promise<void> }) {
  const plannerIsLLM = brief?.interpreted_filters.parser.startsWith('local-llm') ?? false
  return <div className="ai-workspace">
    <section className="ai-hero"><div><p className="label">AI intelligence layer</p><h2>Ask the candidate knowledge base.</h2><p>Search across extracted resumes, skills, projects, education, and work history with grounded retrieval.</p></div><div className="ai-methods"><span>{runtime?.semantic_retrieval_ready ? 'MiniLM semantic search' : 'Semantic retrieval'}</span><span>{runtime?.generation_ready ? 'Local RAG generation' : 'RAG-ready evidence'}</span><span>Explainable sources</span></div></section>
    <section className="ai-runtime surface"><div><p className="label">AI runtime</p><b>{runtime?.embedding_model ?? 'Checking local model'}</b><small>{runtime ? `${runtime.vector_store} · ${runtime.generation_ready ? `Ollama ${runtime.ollama_model}` : 'deterministic grounded summaries'}` : 'Connecting to the AI service'}</small></div><button className="secondary-button" onClick={() => void reindex()} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh knowledge base'}</button></section>
    <section className="ai-query surface"><label><Search size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void run() }} placeholder="e.g. Find backend candidates with FastAPI and retrieval experience" /></label><button className="primary-button" onClick={() => void run()} disabled={loading}>{loading ? <LoaderCircle size={16} className="inline-spinner" /> : <BrainCircuit size={17} />}{loading ? 'Searching' : 'Run fast retrieval'}</button></section>
    {brief ? <section className="ai-results">
      <section className="ai-brief surface"><div><p className="label">Grounded AI brief</p><h3>Evidence before recommendation.</h3></div><p>{brief.answer}</p>
        {brief.interpreted_filters?.has_constraints && <div className="query-plan"><span>Interpreted constraints</span><b>{queryPlanLabel(brief.interpreted_filters)}</b><small>{plannerIsLLM ? 'Planned by local Phi-3 · compiled to safe SQL' : 'Deterministic safe query plan'} · embeddings rank only the matching rows</small></div>}
        <details className="ai-pipeline"><summary><span><BrainCircuit size={16} />AI pipeline trace</span><small>{plannerIsLLM ? 'Local LLM plan + retrieval evidence' : 'Deterministic plan + retrieval evidence'}</small><ChevronRight size={16} /></summary><div className="pipeline-body">
          <article><b>01 · Query interpretation</b><p>{plannerIsLLM ? `Ollama ${runtime?.ollama_model ?? 'Phi-3'} converted the recruiter request into a structured filter plan.` : 'A deterministic parser converted the recruiter request into a structured filter plan.'}</p><pre>{readableQueryPlan(brief.interpreted_filters)}</pre></article>
          <article><b>02 · Safe SQL filtering</b><p>The model does not execute SQL. TalentIQ validates the plan, then compiles it into parameterized SQLAlchemy constraints.</p>{brief.interpreted_filters.sql_preview ? <pre>{brief.interpreted_filters.sql_preview}</pre> : <code>No structured SQL constraints were needed for this query.</code>}</article>
          <article><b>03 · Semantic retrieval and reranking</b><p>{brief.retrieval_method}. MiniLM retrieves profile embeddings from ChromaDB; SQL-filtered candidates remain the only eligible results.</p><div className="pipeline-stat"><span>Retrieved evidence</span><b>{brief.sources.length} profile{brief.sources.length === 1 ? '' : 's'}</b><span>Latency</span><b>{Math.round(brief.retrieval_latency_ms)} ms</b></div></article>
          <article><b>04 · Grounded response</b><p>{brief.generation_mode === 'ollama-rag' ? `Ollama ${runtime?.ollama_model ?? 'Phi-3'} generated the written brief using only the retrieved profile evidence.` : 'This result is retrieval-only. Select “Generate local brief” to ask the local model for a grounded summary.'}</p></article>
        </div></details>
        <footer><span>{brief.semantic_retrieval_active ? 'Live vector retrieval' : 'Retrieval fallback'}</span><span>{brief.generation_mode === 'ollama-rag' ? 'Local LLM synthesis' : 'Retrieval-only evidence'}</span><span>{Math.round(brief.retrieval_latency_ms)} ms · {brief.index_sync.indexed ? `${brief.index_sync.indexed} profile update${brief.index_sync.indexed === 1 ? '' : 's'}` : 'index current'}</span>{runtime?.generation_ready && brief.generation_mode !== 'ollama-rag' && <button className="secondary-button" onClick={() => void run(true)} disabled={loading}><Sparkles size={15} />{loading ? 'Generating locally…' : 'Generate local brief'}</button>}<small>{brief.grounding_note}</small></footer>
      </section>
      <section className="ai-sources surface"><Header label="Retrieved evidence" title={`${brief.sources.length} candidate sources`} />{brief.sources.length ? brief.sources.map((source, index) => <button key={source.id} onClick={() => void openCandidate(source)}><Avatar name={source.full_name} index={index} /><span><b>{source.full_name}</b><small>{source.search_explanation}</small><em>{source.matched_terms.join(' · ')}</em></span><i>{Math.round(source.relevance_score)}%</i><ChevronRight size={17} /></button>) : <Empty text="No candidate satisfied every interpreted constraint." />}</section>
    </section> : <section className="ai-empty surface"><BrainCircuit size={28} /><h3>Semantic candidate discovery</h3><p>Run a natural-language query to retrieve profile evidence and a grounded recruiter brief.</p></section>}
  </div>
}
function StageBadge({ stage }: { stage: PipelineStage }) { return <span className={`stage-badge ${stage}`}>{stageLabel(stage)}</span> }
function Roles({ jobs, job, matches, decisions, compareCandidateIds, chooseJob, openInsight, openUpload, toggleComparison, openComparison }: { jobs: Job[]; job: Job | null; matches: Match[]; decisions: RoleDecision[]; compareCandidateIds: number[]; chooseJob: (job: Job) => void; openInsight: (match: Match) => void; openUpload: () => void; toggleComparison: (candidateId: number) => void; openComparison: () => void }) { return <div className="roles"><aside><header><span>All roles</span></header>{jobs.map((item) => <button className={job?.id === item.id ? 'role active' : 'role'} key={item.id} onClick={() => void chooseJob(item)}><span><b>{item.title ?? 'Untitled role'}</b><small>{item.skills.slice(0, 2).join(' · ') || 'Skills to be defined'}</small></span><ChevronRight size={16} /></button>)}</aside><section>{job ? <><header className="role-head"><div><p className="label">AI fit scoring</p><h2>{job.title}</h2><p>{job.min_experience ?? 0}+ years experience · {job.skills.join(', ')}</p></div><div className="role-actions"><button className="secondary-button compare-button" onClick={openComparison} disabled={compareCandidateIds.length < 2}><GitCompareArrows size={16} />Compare {compareCandidateIds.length || ''}</button><button className="secondary-button" onClick={openUpload}><FileText size={16} />Import job brief</button></div></header><p className="summary"><b>{matches.length}</b> candidates AI analyzed <b>{decisions.filter((item) => item.decision === 'shortlisted' || item.decision === 'interview').length}</b> active selections</p><div className="match-list">{matches.length ? matches.map((match, index) => { const decision = decisions.find((item) => item.candidate_id === match.candidate_id); const selected = compareCandidateIds.includes(match.candidate_id); return <article key={match.candidate_id} className={selected ? 'match-row selected' : 'match-row'}><button className="match-primary" onClick={() => void openInsight(match)}><Avatar name={match.candidate_name} index={index} /><span><b>{match.candidate_name}</b><small>{match.matched_skills.length ? `AI matched: ${match.matched_skills.slice(0, 3).join(', ')}` : 'Review profile evidence'}</small>{decision && <RoleDecisionBadge decision={decision.decision} />}</span><i><b>{Math.round(match.match_score)}%</b><small>AI fit</small></i><ChevronRight size={17} /></button><button className="compare-toggle" title={selected ? `Remove ${match.candidate_name} from comparison` : `Add ${match.candidate_name} to comparison`} aria-pressed={selected} onClick={() => toggleComparison(match.candidate_id)}><CheckCircle2 size={16} /></button></article> }) : <Empty text="No candidate matches yet. Add people to the talent pool." />}</div></> : <Empty text="Create a role to begin AI-assisted review." />}</section></div> }
function RoleDecisionBadge({ decision }: { decision: RoleDecisionStatus }) { return <em className={`role-decision ${decision}`}>{decisionLabel(decision)}</em> }
function Empty({ text }: { text: string }) { return <div className="empty"><Users size={20} /><p>{text}</p></div> }
function Insight({ match, decision, close, saveDecision }: { match: Match; decision?: RoleDecision; close: () => void; saveDecision: (candidateId: number, decision: RoleDecisionStatus, notes: string) => Promise<void> }) { const [selection, setSelection] = useState<RoleDecisionStatus>(decision?.decision ?? 'shortlisted'); const [notes, setNotes] = useState(decision?.notes ?? ''); useEffect(() => { setSelection(decision?.decision ?? 'shortlisted'); setNotes(decision?.notes ?? '') }, [decision, match.candidate_id]); return <aside className="detail-panel insight"><button className="icon-button" title="Close insight" onClick={close}><X size={18} /></button><p className="label">AI match briefing</p><div className="person"><Avatar name={match.candidate_name} index={1} /><div><h2>{match.candidate_name}</h2><p>{match.candidate_experience ?? 0} years experience</p></div></div><div className="recommend"><b>{Math.round(match.match_score)}%</b><span><strong>{match.hiring_recommendation ?? 'Strong match'}</strong><small>{match.recommendation_reason ?? 'Review the evidence below before deciding.'}</small></span></div><p className="description">{match.candidate_summary ?? 'This AI-assisted profile analysis aligns the candidate against role skills and experience.'}</p>{match.score_breakdown && <section className="score-explanation"><div><h3>Why this score</h3><span>Explainable AI</span></div>{match.score_breakdown.map((component) => <article key={component.signal}><header><b>{component.signal}</b><strong>+{Math.round(component.contribution)} pts</strong></header><div><i style={{ width: `${component.contribution}%` }} /></div><small>{component.description} · {component.weight}% weight</small></article>)}<p>{match.fairness_note}</p></section>}<section className="role-decision-editor"><div><h3>Role decision</h3>{decision && <RoleDecisionBadge decision={decision.decision} />}</div><select value={selection} onChange={(event) => setSelection(event.target.value as RoleDecisionStatus)} aria-label="Candidate decision for role"><option value="shortlisted">Shortlist</option><option value="interview">Move to interview</option><option value="rejected">Reject for this role</option></select><textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} placeholder="Capture the decision context for this role." /><button className="primary-button" onClick={() => void saveDecision(match.candidate_id, selection, notes)}>Save decision</button></section><InsightList title="AI signals in their favor" values={match.strengths ?? match.matched_skills} green /><InsightList title="AI points to explore" values={match.weaknesses ?? []} /></aside> }
function ComparisonPanel({ matches, candidates, decisions, close }: { matches: Match[]; candidates: Candidate[]; decisions: RoleDecision[]; close: () => void }) { return <div className="modal-backdrop comparison-backdrop" onMouseDown={close}><section className="comparison-panel" onMouseDown={(event) => event.stopPropagation()}><header><div><p className="label">Finalist comparison</p><h2>Compare the signals</h2></div><button className="icon-button" title="Close comparison" onClick={close}><X size={18} /></button></header><div className="comparison-grid">{matches.map((match, index) => { const candidate = candidates.find((item) => item.id === match.candidate_id); const decision = decisions.find((item) => item.candidate_id === match.candidate_id); return <section key={match.candidate_id}><div className="comparison-person"><Avatar name={match.candidate_name} index={index} /><div><h3>{match.candidate_name}</h3><p>{candidate?.years_experience ?? 0} years experience</p></div></div><div className="comparison-score"><b>{Math.round(match.match_score)}%</b><span>role fit</span></div>{decision && <RoleDecisionBadge decision={decision.decision} />}<ComparisonList title="Matched skills" values={match.matched_skills} /><ComparisonList title="Gaps to review" values={match.weaknesses ?? []} /><ComparisonList title="Decision note" values={decision?.notes ? [decision.notes] : []} /></section> })}</div></section></div> }
function ComparisonList({ title, values }: { title: string; values: string[] }) { return <div className="comparison-list"><h4>{title}</h4>{values.length ? <ul>{values.map((value) => <li key={value}>{value}</li>)}</ul> : <p>None recorded.</p>}</div> }
function CandidateProfile({ candidate, matches, loading, close, openRole, saveWorkflow }: { candidate: Candidate; matches: CandidateRoleMatch[]; loading: boolean; close: () => void; openRole: (match: CandidateRoleMatch) => Promise<void>; saveWorkflow: (candidate: Candidate, pipelineStage: PipelineStage, recruiterNotes: string) => Promise<void> }) { const [stage, setStage] = useState<PipelineStage>(candidate.pipeline_stage); const [notes, setNotes] = useState(candidate.recruiter_notes ?? ''); useEffect(() => { setStage(candidate.pipeline_stage); setNotes(candidate.recruiter_notes ?? '') }, [candidate]); return <aside className="detail-panel candidate-panel"><button className="icon-button" title="Close candidate profile" onClick={close}><X size={18} /></button><p className="label">Candidate profile</p><div className="person"><Avatar name={candidate.full_name} index={2} /><div><h2>{candidate.full_name}</h2><p>{candidate.email}</p></div></div><dl className="candidate-facts"><div><dt>Experience</dt><dd>{candidate.years_experience ?? 0} years</dd></div><div><dt>Profile</dt><dd>{candidate.education?.length || candidate.projects?.length || candidate.certifications?.length ? 'Structured' : 'Basic'}</dd></div></dl><section className="workflow-editor"><div><h3>Pipeline stage</h3><StageBadge stage={stage} /></div><select value={stage} onChange={(event) => setStage(event.target.value as PipelineStage)} aria-label="Candidate pipeline stage">{pipelineStages.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select><label><span>Recruiter notes</span><textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} placeholder="Capture the key follow-up or decision context." /></label><button className="secondary-button" onClick={() => void saveWorkflow(candidate, stage, notes)}>Save workflow</button></section><ProfileSection title="Skills" values={candidate.skills} chip /><ProfileSection title="Work history" values={candidate.work_history ?? []} /><ProfileSection title="Education" values={candidate.education ?? []} /><ProfileSection title="Projects" values={candidate.projects ?? []} /><ProfileSection title="Certifications" values={candidate.certifications ?? []} /><section className="role-recommendations"><h3>AI-suggested roles</h3>{loading ? <p className="panel-loading"><LoaderCircle size={16} />Loading AI suggestions</p> : matches.length ? matches.slice(0, 3).map((match) => <button key={match.job_id} onClick={() => void openRole(match)}><span><b>{match.job_title ?? 'Untitled role'}</b><small>{match.matched_skills.length ? `AI matched: ${match.matched_skills.join(', ')}` : 'Review AI match details'}</small></span><i>{Math.round(match.match_score)}%</i><ChevronRight size={16} /></button>) : <p className="panel-empty">No roles are available to compare yet.</p>}</section></aside> }
function ProfileSection({ title, values, chip = false }: { title: string; values: string[]; chip?: boolean }) { if (!values.length) return null; return <section className={chip ? 'profile-section skills' : 'profile-section'}><h3>{title}</h3>{chip ? <div>{values.map((value) => <i key={value}>{value}</i>)}</div> : <ul>{values.map((value) => <li key={value}>{value}</li>)}</ul>}</section> }
function InsightList({ title, values, green = false }: { title: string; values: string[]; green?: boolean }) { return <section className="insight-list"><h3>{title}</h3>{values.length ? <ul>{values.map((value) => <li key={value}><i className={green ? 'green' : ''}></i>{value}</li>)}</ul> : <p>Nothing notable surfaced.</p>}</section> }
function Modal({ kind, close, save, saving }: { kind: ModalKind; close: () => void; save: (event: FormEvent<HTMLFormElement>, kind: ModalKind) => Promise<void>; saving: boolean }) { const upload = kind === 'resume' || kind === 'brief'; const title = kind === 'candidate' ? 'Add a candidate' : kind === 'job' ? 'Create a new role' : kind === 'resume' ? 'Import a resume' : 'Import a job brief'; const action = upload ? 'Process document' : kind === 'candidate' ? 'Add candidate' : 'Create role'; return <div className="modal-backdrop" onMouseDown={() => !saving && close()}><form className="modal" onSubmit={(event) => void save(event, kind)} onMouseDown={(event) => event.stopPropagation()}><header><div><p className="label">Workspace intake</p><h2>{title}</h2></div><button type="button" className="icon-button" title="Close dialog" onClick={close} disabled={saving}><X size={18} /></button></header>{upload ? <label className="upload"><FileText size={26} /><b>Choose a PDF or DOCX</b><small>We’ll extract the important details for you.</small><input name="file" type="file" accept=".pdf,.docx" required disabled={saving} /></label> : kind === 'candidate' ? <><Field label="Full name" name="name" required /><Field label="Work email" name="email" type="email" required /><div className="two"><Field label="Years of experience" name="experience" type="number" /><Field label="Skills" name="skills" placeholder="React, Python, Strategy" /></div></> : <><Field label="Role title" name="title" required /><div className="two"><Field label="Minimum experience" name="experience" type="number" /><Field label="Core skills" name="skills" placeholder="Figma, Research" /></div><Field label="Key requirements" name="requirements" placeholder="Portfolio, leadership" /><label className="field"><span>Role context</span><textarea name="description" rows={3} placeholder="A concise description makes matching sharper." /></label></>}<button className="primary-button submit" type="submit" disabled={saving}>{saving ? 'Saving...' : action} <ArrowUpRight size={16} /></button></form></div> }
function Field({ label, name, type = 'text', placeholder, required = false }: { label: string; name: string; type?: string; placeholder?: string; required?: boolean }) { return <label className="field"><span>{label}</span><input name={name} type={type} placeholder={placeholder} required={required} min={type === 'number' ? '0' : undefined} /></label> }
