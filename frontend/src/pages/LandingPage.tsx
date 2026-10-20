import { useNavigate } from 'react-router-dom'

/** Marketing-style entry screen. CTA drops the user into the dashboard. */
export default function LandingPage() {
  const navigate = useNavigate()
  return (
    <main className="landing">
      <div className="landing-card">
        <span className="badge">Personal Finance · AI</span>
        <h1>Your money, explained.</h1>
        <p>
          A finance assistant that reads your real spending and answers in plain
          language — budgets, trends, and where your money actually goes.
        </p>

        <div className="landing-cta">
          <button type="button" className="btn-primary" onClick={() => navigate('/dashboard')}>
            Open dashboard →
          </button>
          <button type="button" className="btn-ghost" onClick={() => navigate('/chat')}>
            Start chatting
          </button>
        </div>

        <ul className="features">
          <li>💬 Ask anything about your finances in natural language</li>
          <li>📊 Answers grounded in your real numbers — never guessed</li>
          <li>🎯 Set budgets and savings goals, import your bank CSV</li>
        </ul>
      </div>

      <footer className="landing-footer">Finance Assistant · local dev</footer>
    </main>
  )
}
