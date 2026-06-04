const ROLES = [
    { key: 'student', label: 'Student' },
    { key: 'faculty', label: 'Faculty' },
    { key: 'admin',   label: 'Admin'   },
  ]
  
  export default function Header({ role, onRoleChange, onClear }) {
    return (
      <header className="header">
        {/* Brand */}
        <div className="header-brand">
          <div className="brand-icon" aria-hidden="true">🎓</div>
          <div>
            <div className="brand-name">MindSprout Technologies</div>
            <div className="brand-sub">InstitutionGPT</div>
          </div>
        </div>
  
        {/* Role selector + clear button */}
        <div className="header-right">
          <nav className="role-selector" aria-label="Select your role">
            {ROLES.map(r => (
              <button
                key={r.key}
                className={`role-btn ${r.key} ${role === r.key ? 'active' : ''}`}
                onClick={() => onRoleChange(r.key)}
                aria-pressed={role === r.key}
              >
                {r.label}
              </button>
            ))}
          </nav>
  
          <button className="clear-btn" onClick={onClear} title="Start a new conversation">
            New chat
          </button>
        </div>
      </header>
    )
  }