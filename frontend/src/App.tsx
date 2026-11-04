import { useState, type FormEvent, type ReactNode } from 'react'
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom'
import './App.css'

const practiceQuestion = {
  prompt: 'A garden has 3 rows of flowers. There are 7 flowers in each row. How many flowers are there?',
  answer: '21',
  hint: 'Think of 3 equal groups of 7: 7 + 7 + 7.',
}

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
  const [notice, setNotice] = useState('')

  function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!question.trim()) {
      setNotice('Write a question first, and then try again.')
      return
    }
    setNotice('The chat interface is ready. Tutor connection is the next step; no answer has been generated.')
  }

  return (
    <LearnerLayout>
      <div className="preview-banner"><span aria-hidden="true">ⓘ</span> Interface preview · tutor connection is not active yet</div>
      <div className="page-heading learner-heading">
        <span className="eyebrow">YOUR MATHS SPACE</span>
        <h1>What are you wondering?</h1>
        <p>Ask a maths question and explore it one step at a time.</p>
      </div>
      <section className="chat-card" aria-label="Tutor chat preview">
        <div className="chat-welcome">
          <div className="chat-avatar" aria-hidden="true">✳</div>
          <div>
            <strong>Your maths tutor</strong>
            <p>When connected, this is where your explanation will appear.</p>
          </div>
        </div>
        <div className="suggestion-row" aria-label="Example questions">
          {['How do fractions work?', 'Can you show me multiplication?', 'What is a number line?'].map((suggestion) => (
            <button key={suggestion} className="suggestion-chip" type="button" onClick={() => setQuestion(suggestion)}>
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
          />
          <div className="form-footer">
            <span>Ask anything about maths</span>
            <button className="button button-primary learner-button" type="submit">Send question <span aria-hidden="true">↑</span></button>
          </div>
        </form>
        {notice && <p className="inline-notice" role="status">{notice}</p>}
      </section>
    </LearnerLayout>
  )
}

function PracticePage() {
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState<'correct' | 'try-again' | ''>('')

  function checkAnswer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFeedback(answer.trim() === practiceQuestion.answer ? 'correct' : 'try-again')
  }

  return (
    <LearnerLayout>
      <div className="preview-banner"><span aria-hidden="true">ⓘ</span> Sample exercise · answers are checked in this browser only</div>
      <div className="page-heading learner-heading">
        <span className="eyebrow">GUIDED PRACTICE</span>
        <h1>Try it your way.</h1>
        <p>Work through a question, and use the hint if you need a nudge.</p>
      </div>
      <section className="practice-card">
        <div className="exercise-meta"><span>Sample question</span><span>Multiplication</span></div>
        <div className="array-visual" aria-label="Three groups of seven dots">
          {[0, 1, 2].map((row) => (
            <div className="dot-row" key={row}>
              {Array.from({ length: 7 }, (_, dot) => <span className="math-dot" key={dot} />)}
            </div>
          ))}
        </div>
        <h2>{practiceQuestion.prompt}</h2>
        <form className="practice-form" onSubmit={checkAnswer}>
          <label htmlFor="practice-answer">Your answer</label>
          <div className="answer-row">
            <input id="practice-answer" inputMode="numeric" value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Type a number" />
            <button className="button button-primary learner-button" type="submit">Check answer</button>
          </div>
        </form>
        <details className="hint-panel">
          <summary>I'd like a hint</summary>
          <p>{practiceQuestion.hint}</p>
        </details>
        {feedback === 'correct' && <p className="feedback success" role="status">That's right! You found 3 groups of 7.</p>}
        {feedback === 'try-again' && <p className="feedback encouragement" role="status">Not quite yet. Try counting the groups, or open the hint above.</p>}
        <p className="small-print">This sample exercise does not save scores or learner progress.</p>
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

  return (
    <TeacherLayout>
      <div className="preview-banner teacher-banner"><span aria-hidden="true">ⓘ</span> Editable template · sample text only, not generated lesson content</div>
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
        </div>
        <div className="lesson-title">
          <span className="eyebrow">{grade} · {duration}</span>
          <h2>{topic || 'Untitled lesson'}</h2>
          <p>Editable sample outline — lesson generation is not connected.</p>
        </div>
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
