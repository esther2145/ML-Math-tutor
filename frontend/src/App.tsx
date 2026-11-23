import { useState, type FormEvent, type ReactNode } from 'react'
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom'
import {
  askTutor,
  generateLessonPlan,
  type BloomLevel,
  type LessonPlanResponse,
  type RetrievedMaterial,
  type RetrievalTrace,
  type VerificationResult,
} from './services/tutorApi'
import './App.css'

type PracticeQuestion = {
  topic: string
  prompt: string
  answer: string
  hint: string
  visualLabel: string
  rows: { label: string; count: number; removedCount?: number }[]
  success: string
}

const practiceQuestions: PracticeQuestion[] = [
  {
    topic: 'Multiplication',
    prompt: 'A garden has 3 rows of flowers. There are 7 flowers in each row. How many flowers are there?',
    answer: '21',
    hint: 'Count 7 flowers in each of 3 rows: 7 + 7 + 7.',
    visualLabel: 'Three rows of seven flowers each.',
    rows: [
      { label: 'Row 1', count: 7 },
      { label: 'Row 2', count: 7 },
      { label: 'Row 3', count: 7 },
    ],
    success: 'That’s right! Three groups of 7 make 21.',
  },
  {
    topic: 'Addition',
    prompt: 'Mia has 8 red beads and 5 blue beads. How many beads does she have altogether?',
    answer: '13',
    hint: 'Put the two groups together: 8 + 5.',
    visualLabel: 'A group of eight red beads and a group of five blue beads.',
    rows: [
      { label: 'Red beads', count: 8 },
      { label: 'Blue beads', count: 5 },
    ],
    success: 'Correct! 8 beads and 5 beads make 13.',
  },
  {
    topic: 'Subtraction',
    prompt: 'There are 14 apples in a basket. If 6 are given away, how many are left?',
    answer: '8',
    hint: 'Start with 14 and take away the 6 crossed-out apples.',
    visualLabel: 'Fourteen apples, with six crossed out.',
    rows: [{ label: 'Apples', count: 14, removedCount: 6 }],
    success: 'That’s right! 8 apples are left.',
  },
  {
    topic: 'Division',
    prompt: 'Share 12 oranges equally between 3 baskets. How many oranges go in each basket?',
    answer: '4',
    hint: 'Share the oranges equally so each basket has the same number.',
    visualLabel: 'Three baskets with four oranges shared into each basket.',
    rows: [
      { label: 'Basket 1', count: 4 },
      { label: 'Basket 2', count: 4 },
      { label: 'Basket 3', count: 4 },
    ],
    success: 'Correct! Each basket gets 4 oranges.',
  },
]

const lessonSections = [
  ['Learning objectives', 'By the end of the lesson, learners can…'],
  ['Prerequisite knowledge', 'What should learners already know?'],
  ['Warm-up activity', 'A short activity to introduce the topic…'],
  ['Main explanation and worked examples', 'Explain the idea step by step…'],
  ['Guided and independent practice', 'Practice questions for learners…'],
  ['Assessment and answer key', 'Questions to check understanding…'],
]

function Brand() {
  return (
    <Link className="brand" to="/" aria-label="G-RAFT home">
      <span className="brand-mark" aria-hidden="true">g</span>
      <span>G-RAFT<span className="brand-subtitle">MATH LEARNING</span></span>
    </Link>
  )
}

function SiteHeader() {
  const location = useLocation()
  const isLearner = location.pathname.startsWith('/learn')
  const isTeacher = location.pathname.startsWith('/teacher')

  return (
    <header className="site-header">
      <Brand />
      <nav className="top-nav" aria-label="Main navigation">
        <NavLink to="/learn" className={isLearner ? 'active' : ''}>Learner</NavLink>
        <NavLink to="/teacher" className={isTeacher ? 'active' : ''}>Teacher</NavLink>
      </nav>
      <span className="prototype-label">Prototype</span>
    </header>
  )
}

function AppFrame({ children }: { children: ReactNode }) {
  return (
    <div className="app-frame">
      <SiteHeader />
      {children}
    </div>
  )
}

function WelcomePage() {
  return (
    <AppFrame>
      <main className="welcome-page">
        <div className="welcome-copy">
          <span className="eyebrow">A mathematics companion for every classroom</span>
          <h1>Big ideas start<br />with <span className="highlight">one question.</span></h1>
          <p>Explore maths together. Choose the space that fits what you need today.</p>
        </div>
        <div className="role-grid">
          <Link className="role-card learner-card" to="/learn">
            <div className="role-icon learner-icon" aria-hidden="true">✳</div>
            <span className="eyebrow">For curious minds</span>
            <h2>I'm a learner</h2>
            <p>Ask questions, explore examples, and practise at your own pace.</p>
            <span className="card-link">Start learning <span aria-hidden="true">→</span></span>
          </Link>
          <Link className="role-card teacher-card" to="/teacher">
            <div className="role-icon teacher-icon" aria-hidden="true">▤</div>
            <span className="eyebrow">For educators</span>
            <h2>I'm a teacher</h2>
            <p>Explore concepts, teaching approaches, and lesson planning tools.</p>
            <span className="card-link">Open teaching space <span aria-hidden="true">→</span></span>
          </Link>
        </div>
        <p className="welcome-note">Choose a space to explore the G-RAFT prototype. This is not an account or identity check.</p>
      </main>
    </AppFrame>
  )
}

function LearnerLayout({ children }: { children: ReactNode }) {
  return (
    <AppFrame>
      <div className="workspace learner-workspace">
        <aside className="workspace-sidebar">
          <div className="sidebar-heading">LEARNER SPACE</div>
          <NavLink to="/learn" end className={({ isActive }) => `side-link${isActive ? ' selected' : ''}`}>
            <span aria-hidden="true">✳</span> Ask the tutor
          </NavLink>
          <NavLink to="/learn/practice" className={({ isActive }) => `side-link${isActive ? ' selected' : ''}`}>
            <span aria-hidden="true">◉</span> Guided practice
          </NavLink>
          <div className="sidebar-tip">
            <span className="tip-spark" aria-hidden="true">✦</span>
            <strong>Maths is for everyone.</strong>
            <p>Take your time. Every question is a good place to start.</p>
          </div>
        </aside>
        <main className="workspace-main learner-main">{children}</main>
      </div>
    </AppFrame>
  )
}

function LearnerTutorPage() {
  const [question, setQuestion] = useState('')
  const [learnerGrade, setLearnerGrade] = useState(3)
  const [messages, setMessages] = useState<
    {
      id: number
      role: 'user' | 'assistant'
      content: string
      verification?: VerificationResult
      retrievedMaterials?: RetrievedMaterial[]
      retrievalTrace?: RetrievalTrace
    }[]
  >([])
  const [error, setError] = useState('')
  const [isSending, setIsSending] = useState(false)

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || isSending) {
      return
    }

    setError('')
    setQuestion('')
    setMessages((current) => [
      ...current,
      {
        id: Date.now(),
        role: 'user',
        content: trimmedQuestion,
      },
    ])
    setIsSending(true)

    try {
      const result = await askTutor(trimmedQuestion, learnerGrade)
      setMessages((current) => [
        ...current,
        {
          id: Date.now(),
          role: 'assistant',
          content: result.answer,
          verification: result.verification,
          retrievedMaterials: result.retrieved_materials,
          retrievalTrace: result.retrieval_trace,
        },
      ])
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'An unexpected error occurred while contacting the tutor.',
      )
    } finally {
      setIsSending(false)
    }
  }

  return (
    <LearnerLayout>
      <div className="preview-banner"><span aria-hidden="true">ⓘ</span> Connected to the tutor API · each question is sent independently</div>
      <div className="page-heading learner-heading">
        <span className="eyebrow">YOUR MATHS SPACE</span>
        <h1>What are you wondering?</h1>
        <p>Ask a maths question. Choose a level to help shape the explanation.</p>
      </div>
      <section className="chat-card" aria-label="Tutor chat">
        <div className="learner-settings">
          <label htmlFor="learner-grade">Learner level</label>
          <select
            id="learner-grade"
            value={learnerGrade}
            onChange={(event) => setLearnerGrade(Number(event.target.value))}
            disabled={isSending}
          >
            {Array.from({ length: 7 }, (_, index) => index + 1).map((grade) => (
              <option key={grade} value={grade}>Primary {grade}</option>
            ))}
          </select>
        </div>
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <div className="chat-avatar" aria-hidden="true">✳</div>
            <div>
              <strong>Your maths tutor</strong>
              <p>Send a question to get an explanation from the G-RAFT backend.</p>
            </div>
          </div>
        ) : (
          <div className="chat-messages" aria-live="polite">
            {messages.map((message) => (
              <article className={`chat-message ${message.role}`} key={message.id}>
                <span className="message-author">
                  {message.role === 'user' ? 'You' : 'G-RAFT tutor'}
                </span>
                <p>{message.content}</p>
                {message.role === 'assistant' && (
                  <>
                    {message.verification && (
                      <VerificationNotice verification={message.verification} />
                    )}
                    {(message.retrievedMaterials?.length || message.retrievalTrace) && (
                      <RetrievalDetails
                        materials={message.retrievedMaterials ?? []}
                        trace={message.retrievalTrace}
                      />
                    )}
                  </>
                )}
              </article>
            ))}
          </div>
        )}
        {isSending && <p className="sending-status" role="status">The tutor is preparing a response…</p>}
        {error && <p className="api-error" role="alert">{error}</p>}
        <div className="suggestion-row" aria-label="Example questions">
          {['How do fractions work?', 'Can you show me multiplication?', 'What is a number line?'].map((suggestion) => (
            <button
              key={suggestion}
              className="suggestion-chip"
              type="button"
              disabled={isSending}
              onClick={() => setQuestion(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
        <form className="question-form" onSubmit={submitQuestion}>
          <label className="visually-hidden" htmlFor="learner-question">Your maths question</label>
          <textarea
            id="learner-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Type your question here…"
            rows={2}
            disabled={isSending}
          />
          <div className="form-footer">
            <span>Requests are sent as standalone questions</span>
            <button
              className="button button-primary learner-button"
              type="submit"
              disabled={isSending || !question.trim()}
            >
              {isSending ? 'Sending…' : 'Send question'} <span aria-hidden="true">↑</span>
            </button>
          </div>
        </form>
      </section>
    </LearnerLayout>
  )
}

function VerificationNotice({ verification }: { verification: VerificationResult }) {
  let message: string
  if (verification.check === 'evidence_references') {
    if (verification.reference_status === 'passed') {
      message =
        'Evidence references are valid; whether they support each claim is not verified.'
    } else if (verification.reference_status === 'failed') {
      message =
        `Evidence citation check failed after ${verification.refinement_attempts ?? 0} correction attempt(s). Claim accuracy is not verified.`
    } else {
      message =
        'No retrieved evidence was available. This answer was not generated from curriculum evidence.'
    }
  } else if (verification.status === 'passed') {
    message =
      'Arithmetic result check passed. The explanation and reasoning are not verified.'
  } else if (verification.status === 'failed') {
    message = 'Arithmetic result check failed. Please review this answer.'
  } else {
    message =
      'Not checked by the arithmetic verifier; this does not mean the answer is verified.'
  }

  return (
    <div className={`verification-notice ${verification.status}`} role="status">
      {message}
    </div>
  )
}

function RetrievalDetails({
  materials,
  trace,
}: {
  materials: RetrievedMaterial[]
  trace?: RetrievalTrace
}) {
  return (
    <details className="retrieval-details">
      <summary>Inspect retrieval details (not a proof of correctness)</summary>
      {trace?.vector_search && (
        <div className="trace-summary">
          <strong>Material search:</strong> {trace.vector_search.hit_count ?? materials.length} result(s)
          {' · '}status: {trace.vector_search.status ?? 'unknown'}
          {trace.vector_search.minimum_score != null
            ? ` · minimum score: ${trace.vector_search.minimum_score}`
            : ''}
        </div>
      )}
      {materials.length > 0 ? (
        <ul className="retrieved-material-list">
          {materials.map((material, index) => (
            <li key={`${material.id ?? material.title ?? 'material'}-${index}`}>
              <strong>Evidence [M{index + 1}]</strong>
              <strong>{material.title ?? 'Untitled material'}</strong>
              <span>
                {material.topic ?? 'Topic not specified'}
                {material.grade != null ? ` · Primary ${material.grade}` : ''}
                {material.score != null ? ` · score ${material.score}` : ''}
              </span>
              {material.content && <p>{material.content}</p>}
              <span>
                Source: {material.source_title ?? 'not recorded'}
                {material.source_page ? ` · page ${material.source_page}` : ''}
                {material.source_status ? ` · ${material.source_status}` : ''}
              </span>
              {material.source_url && (
                <a href={material.source_url} target="_blank" rel="noreferrer">
                  Open source
                </a>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="trace-empty">No vector materials were returned.</p>
      )}
      {trace?.graph_lookup && (
        <div className="graph-trace">
          <strong>
            {trace.graph_lookup.status === 'found'
              ? 'Graph evidence [G1] · lookup:'
              : 'Graph lookup:'}
          </strong>{' '}
          {trace.graph_lookup.status ?? 'unknown'}
          {trace.graph_lookup.topic ? ` · ${trace.graph_lookup.topic}` : ''}
          {trace.graph_lookup.node_id ? ` · node ${trace.graph_lookup.node_id}` : ''}
          {trace.graph_lookup.provenance_status === 'not_recorded' && (
            <p>Source provenance for this graph node is not recorded.</p>
          )}
        </div>
      )}
    </details>
  )
}

function PracticePage() {
  const [questionIndex, setQuestionIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState<'correct' | 'try-again' | ''>('')
  const question = practiceQuestions[questionIndex]

  function checkAnswer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFeedback(answer.trim() === question.answer ? 'correct' : 'try-again')
  }

  function moveToNextQuestion() {
    setQuestionIndex((current) => current + 1)
    setAnswer('')
    setFeedback('')
  }

  function restartPractice() {
    setQuestionIndex(0)
    setAnswer('')
    setFeedback('')
  }

  return (
    <LearnerLayout>
      <div className="preview-banner"><span aria-hidden="true">ⓘ</span> Guided exercises · answers are checked in this browser only</div>
      <div className="page-heading learner-heading">
        <span className="eyebrow">GUIDED PRACTICE</span>
        <h1>Try it your way.</h1>
        <p>Work through a question, and use the hint if you need a nudge.</p>
      </div>
      <section className="practice-card">
        {question ? (
          <>
            <div className="exercise-meta">
              <span>Question {questionIndex + 1} of {practiceQuestions.length}</span>
              <span>{question.topic}</span>
            </div>
            <progress
              className="practice-progress"
              value={questionIndex + 1}
              max={practiceQuestions.length}
              aria-label={`Question ${questionIndex + 1} of ${practiceQuestions.length}`}
            />
            <div className="array-visual" role="img" aria-label={question.visualLabel}>
              {question.rows.map((row) => (
                <div className="dot-group" key={row.label}>
                  <span className="dot-group-label">{row.label}</span>
                  <div className="dot-row" aria-hidden="true">
                    {Array.from({ length: row.count }, (_, dot) => (
                      <span
                        className={`math-dot${dot < (row.removedCount ?? 0) ? ' removed' : ''}`}
                        key={dot}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <h2>{question.prompt}</h2>
            <form className="practice-form" onSubmit={checkAnswer}>
              <label htmlFor="practice-answer">Your answer</label>
              <div className="answer-row">
                <input
                  id="practice-answer"
                  inputMode="numeric"
                  value={answer}
                  onChange={(event) => setAnswer(event.target.value)}
                  placeholder="Type a number"
                  disabled={feedback === 'correct'}
                />
                <button
                  className="button button-primary learner-button"
                  type="submit"
                  disabled={!answer.trim() || feedback === 'correct'}
                >
                  Check answer
                </button>
              </div>
            </form>
            <details className="hint-panel">
              <summary>I'd like a hint</summary>
              <p>{question.hint}</p>
            </details>
            {feedback === 'correct' && (
              <>
                <p className="feedback success" role="status">{question.success}</p>
                <button
                  className="button button-primary practice-next"
                  type="button"
                  onClick={moveToNextQuestion}
                >
                  Next question <span aria-hidden="true">→</span>
                </button>
              </>
            )}
            {feedback === 'try-again' && (
              <p className="feedback encouragement" role="status">
                Not quite yet. Try counting the groups, or open the hint above.
              </p>
            )}
          </>
        ) : (
          <div className="practice-complete" role="status">
            <span className="eyebrow">PRACTICE COMPLETE</span>
            <h2>Nice work!</h2>
            <p>You’ve tried all {practiceQuestions.length} visual questions.</p>
            <button
              className="button button-primary"
              type="button"
              onClick={restartPractice}
            >
              Practise again
            </button>
          </div>
        )}
        <p className="small-print">These sample exercises are checked in this browser only. Scores and progress are not saved.</p>
      </section>
    </LearnerLayout>
  )
}

function TeacherLayout({ children }: { children: ReactNode }) {
  return (
    <AppFrame>
      <div className="workspace teacher-workspace">
        <aside className="workspace-sidebar teacher-sidebar">
          <div className="sidebar-heading">TEACHER WORKSPACE</div>
          <NavLink to="/teacher" end className={({ isActive }) => `side-link${isActive ? ' selected' : ''}`}>
            <span aria-hidden="true">⌕</span> Teaching assistant
          </NavLink>
          <NavLink to="/teacher/lesson" className={({ isActive }) => `side-link${isActive ? ' selected' : ''}`}>
            <span aria-hidden="true">▤</span> Lesson outline
          </NavLink>
          <div className="sidebar-tip teacher-tip">
            <strong>Built to support your judgement</strong>
            <p>Generated teaching ideas should always be reviewed and adapted to your class.</p>
          </div>
        </aside>
        <main className="workspace-main teacher-main">{children}</main>
      </div>
    </AppFrame>
  )
}

function TeacherAssistantPage() {
  const [prompt, setPrompt] = useState('')
  const [grade, setGrade] = useState('Primary 4')
  const [notice, setNotice] = useState('')

  function submitRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!prompt.trim()) {
      setNotice('Add a teaching question before submitting.')
      return
    }
    setNotice('Your request is ready to send. Teaching-assistant generation is not connected yet.')
  }

  return (
    <TeacherLayout>
      <div className="preview-banner teacher-banner"><span aria-hidden="true">ⓘ</span> Workspace preview · no teaching content is generated yet</div>
      <div className="page-heading teacher-heading">
        <span className="eyebrow">PREPARATION SPACE</span>
        <h1>Plan with a little more clarity.</h1>
        <p>Explore a topic, consider prerequisites, and prepare ideas for your classroom.</p>
      </div>
      <section className="teacher-form-card">
        <form onSubmit={submitRequest}>
          <label htmlFor="teacher-question">What would you like to explore?</label>
          <textarea id="teacher-question" rows={4} value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="For example: What misconceptions might learners have about equivalent fractions?" />
          <div className="teacher-form-footer">
            <label htmlFor="teacher-grade">Learner level
              <select id="teacher-grade" value={grade} onChange={(event) => setGrade(event.target.value)}>
                {Array.from({ length: 7 }, (_, index) => `Primary ${index + 1}`).map((level) => <option key={level}>{level}</option>)}
              </select>
            </label>
            <button className="button button-dark" type="submit">Prepare request <span aria-hidden="true">→</span></button>
          </div>
          {notice && <p className="inline-notice" role="status">{notice}</p>}
        </form>
      </section>
      <div className="teacher-prompt-list">
        <h2>Questions you could explore</h2>
        <div className="prompt-grid">
          {[
            'What should learners understand before multiplication?',
            'Suggest an activity for teaching fractions.',
            'Give me a worked example of division.',
          ].map((example) => (
            <button className="prompt-card" key={example} type="button" onClick={() => setPrompt(example)}>
              <span aria-hidden="true">↗</span>{example}
            </button>
          ))}
        </div>
      </div>
    </TeacherLayout>
  )
}

function LessonOutlinePage() {
  const [topic, setTopic] = useState('')
  const [grade, setGrade] = useState('Primary 4')
  const [duration, setDuration] = useState('40 minutes')
  const [bloomLevel, setBloomLevel] = useState<BloomLevel>('Apply')
  const [competency, setCompetency] = useState('')
  const [assessmentEvidence, setAssessmentEvidence] = useState('')
  const [lessonPlan, setLessonPlan] = useState<LessonPlanResponse | null>(null)
  const [generationError, setGenerationError] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)

  async function createLessonPlan() {
    if (!topic.trim() || !competency.trim() || !assessmentEvidence.trim()) {
      setGenerationError(
        'Enter a topic, measurable competency, and assessment criteria before generating.',
      )
      return
    }

    setGenerationError('')
    setLessonPlan(null)
    setIsGenerating(true)
    try {
      const result = await generateLessonPlan({
        topic: topic.trim(),
        learner_grade: Number(grade.replace('Primary ', '')),
        duration_minutes: Number.parseInt(duration, 10),
        bloom_level: bloomLevel,
        competency: competency.trim(),
        assessment_criteria: assessmentEvidence.trim(),
        country_code: 'UG',
      })
      setLessonPlan(result)
    } catch (error) {
      setGenerationError(
        error instanceof Error
          ? error.message
          : 'An unexpected error occurred while generating the lesson draft.',
      )
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <TeacherLayout>
      <div className="preview-banner teacher-banner"><span aria-hidden="true">ⓘ</span> AI-generated lesson drafts require teacher review and curriculum checking</div>
      <div className="page-heading teacher-heading">
        <span className="eyebrow">LESSON PLANNER</span>
        <h1>Shape a lesson outline.</h1>
        <p>Set the context, then edit each section to fit your learners.</p>
      </div>
      <section className="lesson-card">
        <div className="lesson-settings">
          <label>Topic<input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="e.g. Equivalent fractions" /></label>
          <label>Level<select value={grade} onChange={(event) => setGrade(event.target.value)}>{Array.from({ length: 7 }, (_, index) => `Primary ${index + 1}`).map((level) => <option key={level}>{level}</option>)}</select></label>
          <label>Duration<select value={duration} onChange={(event) => setDuration(event.target.value)}>{['30 minutes', '40 minutes', '60 minutes'].map((time) => <option key={time}>{time}</option>)}</select></label>
          <label>Bloom's cognitive level
            <select
              value={bloomLevel}
              onChange={(event) => {
                const selectedLevel = event.target.value
                if (
                  selectedLevel === 'Remember' ||
                  selectedLevel === 'Understand' ||
                  selectedLevel === 'Apply' ||
                  selectedLevel === 'Analyse' ||
                  selectedLevel === 'Evaluate' ||
                  selectedLevel === 'Create'
                ) {
                  setBloomLevel(selectedLevel)
                }
              }}
            >
              {['Remember', 'Understand', 'Apply', 'Analyse', 'Evaluate', 'Create'].map((level) => (
                <option key={level} value={level}>{level}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="competency-planner">
          <label htmlFor="lesson-competency">Learner competency / measurable outcome</label>
          <textarea
            id="lesson-competency"
            rows={2}
            value={competency}
            onChange={(event) => setCompetency(event.target.value)}
            placeholder="By the end of the lesson, learners will be able to…"
          />
          <p>Describe what learners will demonstrate, not only what the teacher will cover.</p>
          <label htmlFor="assessment-evidence">Assessment evidence / success criteria</label>
          <textarea
            id="assessment-evidence"
            rows={2}
            value={assessmentEvidence}
            onChange={(event) => setAssessmentEvidence(event.target.value)}
            placeholder="What will learners do or produce to show this competency?"
          />
          <p>Example: Solve 4 out of 5 equivalent-fraction problems and explain one method.</p>
        </div>
        <div className="lesson-title">
          <span className="eyebrow">{grade} · {duration} · Bloom: {bloomLevel}</span>
          <h2>{topic || 'Untitled lesson'}</h2>
          <p>Competency-based planning template — suggestions are teacher-entered and need curriculum review.</p>
          {competency && <p><strong>Target competency:</strong> {competency}</p>}
          {assessmentEvidence && <p><strong>Evidence of learning:</strong> {assessmentEvidence}</p>}
        </div>
        <div className="lesson-generation-controls">
          <button
            className="button button-dark"
            type="button"
            onClick={createLessonPlan}
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating draft…' : 'Generate lesson draft'}
          </button>
          {generationError && <p className="api-error" role="alert">{generationError}</p>}
        </div>
        {lessonPlan && (
          <section className="generated-lesson" aria-live="polite">
            <h3>AI-generated draft · review before use</h3>
            <p>
              {lessonPlan.evidence_status === 'reviewed_materials_retrieved'
                ? 'Reviewed curriculum material was retrieved. Check every suggested activity against your curriculum.'
                : 'No reviewed Uganda curriculum material was retrieved. This is a general draft, not a curriculum-validated lesson.'}
            </p>
            <pre>{lessonPlan.lesson_plan}</pre>
            {lessonPlan.retrieved_materials.length > 0 && (
              <ul>
                {lessonPlan.retrieved_materials.map((material, index) => (
                  <li key={`${material.id ?? material.title ?? 'source'}-${index}`}>
                    [M{index + 1}] {material.source_title ?? material.title ?? 'Reviewed material'}
                    {material.source_page ? ` · page ${material.source_page}` : ''}
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}
        <div className="lesson-sections">
          {lessonSections.map(([title, placeholder], index) => (
            <label className="lesson-section" key={title}>
              <span className="section-number">{String(index + 1).padStart(2, '0')}</span>
              <span className="section-content"><strong>{title}</strong><textarea rows={2} placeholder={placeholder} /></span>
            </label>
          ))}
        </div>
        <div className="lesson-actions">
          <span>Changes stay in this page and are not saved.</span>
          <button className="button button-dark" type="button" onClick={() => window.print()}>Print outline <span aria-hidden="true">↗</span></button>
        </div>
      </section>
    </TeacherLayout>
  )
}

function NotFoundPage() {
  return (
    <AppFrame>
      <main className="not-found">
        <span className="eyebrow">PAGE NOT FOUND</span>
        <h1>Let's find our way back.</h1>
        <Link className="button button-dark" to="/">Return home</Link>
      </main>
    </AppFrame>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/learn" element={<LearnerTutorPage />} />
        <Route path="/learn/practice" element={<PracticePage />} />
        <Route path="/teacher" element={<TeacherAssistantPage />} />
        <Route path="/teacher/lesson" element={<LessonOutlinePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
