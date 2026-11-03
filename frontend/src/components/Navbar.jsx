export default function Navbar({ activeView, onNavigate, views }) {
  return (
    <header className="navbar">
      <strong>CropCapture</strong>
      <nav className="nav-actions">
        <button
          className={activeView === views.FIELD_ENTRY ? "active" : ""}
          onClick={() => onNavigate(views.FIELD_ENTRY)}
          type="button"
        >
          Field Entry
        </button>
        <button
          className={activeView === views.QUERY ? "active" : ""}
          onClick={() => onNavigate(views.QUERY)}
          type="button"
        >
          Query Records
        </button>
        <button
          className={activeView === views.SEED_INVENTORY ? "active" : ""}
          onClick={() => onNavigate(views.SEED_INVENTORY)}
          type="button"
        >
          Seed Inventory
        </button>
      </nav>
    </header>
  );
}
