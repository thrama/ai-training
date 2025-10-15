#!/usr/bin/env python3
"""
EDC Explorer Launcher - FIXED VERSION
Script per avviare l'interfaccia Terminal UI con controlli preliminari.
Gestisce automaticamente i path e le dipendenze.
"""
import sys
import os
from pathlib import Path

def detect_project_structure():
    """Rileva automaticamente la struttura del progetto."""
    current_dir = Path(__file__).parent
    
    print("🔍 Detecting project structure...")
    print(f"   Current directory: {current_dir}")
    
    # Scenario 1: Siamo nella directory principale del progetto
    src_path = current_dir / "src"
    if src_path.exists():
        print(f"   ✅ Found src/ in current directory")
        return current_dir, True
    
    # Scenario 2: Siamo in una subdirectory, il progetto è un livello sopra
    parent_dir = current_dir.parent
    src_path = parent_dir / "src"
    if src_path.exists():
        print(f"   ✅ Found src/ in parent directory: {parent_dir}")
        return parent_dir, True
    
    # Scenario 3: Cerchiamo nei directory sopra (max 3 livelli)
    for i in range(3):
        check_dir = current_dir.parent.parent if i == 0 else current_dir.parents[i+1]
        src_path = check_dir / "src"
        if src_path.exists():
            print(f"   ✅ Found src/ at: {check_dir}")
            return check_dir, True
    
    print(f"   ⚠️ src/ directory not found - will use mock mode")
    return current_dir, False

def check_dependencies():
    """Verifica le dipendenze necessarie."""
    print("\n🔧 Checking dependencies...")
    
    required_packages = [
        ('textual', 'Textual UI framework', True),
        ('aiohttp', 'Async HTTP client', False),
        ('pydantic', 'Data validation', False),
        ('anthropic', 'Claude API', False),
    ]
    
    missing_critical = []
    missing_optional = []
    
    for package, description, critical in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package} - {description}")
        except ImportError:
            print(f"   ❌ {package} - {description} (MISSING)")
            if critical:
                missing_critical.append(package)
            else:
                missing_optional.append(package)
    
    if missing_critical:
        print(f"\n❌ Critical dependencies missing: {', '.join(missing_critical)}")
        print("Install with: pip install textual")
        return False
    
    if missing_optional:
        print(f"\n⚠️ Optional dependencies missing: {', '.join(missing_optional)}")
        print("Some features may not work. Install with:")
        print("pip install aiohttp pydantic anthropic")
    
    return True

def check_terminal_capabilities():
    """Verifica le capacità del terminale."""
    print("\n🎨 Checking terminal capabilities...")
    
    # Verifica variabili ambiente terminale
    term = os.environ.get('TERM', 'unknown')
    colorterm = os.environ.get('COLORTERM', 'unknown')
    
    print(f"   TERM: {term}")
    print(f"   COLORTERM: {colorterm}")
    
    # Verifica dimensioni
    try:
        import shutil
        size = shutil.get_terminal_size()
        print(f"   Terminal size: {size.columns}x{size.lines}")
        
        if size.columns < 80 or size.lines < 24:
            print("   ⚠️ Terminal size might be too small")
            print("   Recommended: 120x40 or larger")
        else:
            print("   ✅ Terminal size OK")
            
    except Exception as e:
        print(f"   ⚠️ Could not detect terminal size: {e}")
    
    return True

def setup_environment(project_root: Path, has_real_modules: bool):
    """Setup dell'ambiente Python."""
    print(f"\n⚙️ Setting up environment...")
    
    # Aggiungi project root al Python path
    sys.path.insert(0, str(project_root))
    print(f"   Added to Python path: {project_root}")
    
    # Imposta variabili ambiente se necessario
    if not has_real_modules:
        os.environ['EDC_MOCK_MODE'] = 'true'
        print("   Set EDC_MOCK_MODE=true (no real modules found)")
    
    # Verifica/imposta variabili terminale per performance ottimali
    if not os.environ.get('TERM'):
        os.environ['TERM'] = 'xterm-256color'
        print("   Set TERM=xterm-256color")
    
    if not os.environ.get('COLORTERM'):
        os.environ['COLORTERM'] = 'truecolor'
        print("   Set COLORTERM=truecolor")
    
    return True

def create_css_if_missing():
    """Crea file CSS se mancante."""
    css_file = Path("edc_explorer.css")
    
    if css_file.exists():
        print(f"   ✅ CSS file found: {css_file}")
        return
    
    print(f"   📝 Creating default CSS file: {css_file}")
    
    default_css = """/* EDC Explorer Default CSS */
App {
    background: $surface;
}

Header {
    background: $primary;
    color: $text;
    text-style: bold;
}

Footer {
    background: $primary-darken-1;
    color: $text;
}

.section-title {
    background: $primary-lighten-1;
    color: $text;
    text-style: bold;
    padding: 1;
    margin-bottom: 1;
    text-align: center;
}

.subsection-title {
    background: $secondary;
    color: $text;
    text-style: bold;
    padding: 0 1;
    margin-bottom: 1;
}

/* Search controls */
.search-controls {
    height: 3;
    margin-bottom: 1;
    align: center middle;
}

.search-controls Input {
    margin-right: 1;
    min-width: 20;
}

.search-controls Select {
    margin-right: 1;
    min-width: 15;
}

.search-controls Button {
    margin-left: 1;
}

/* Results layout */
.results-section {
    height: 1fr;
}

.search-results {
    width: 60%;
    margin-right: 1;
    border: thick $primary;
}

.asset-details {
    width: 40%;
    border: thick $secondary;
}

/* Common widgets */
Input {
    border: solid $primary;
}

Input:focus {
    border: solid $accent;
}

Button {
    margin: 0 1;
    min-width: 10;
}

Button.-primary {
    background: $primary;
    color: $text;
}

Button.-secondary {
    background: $secondary;
    color: $text;
}

DataTable {
    background: $surface;
}

DataTable > .datatable--header {
    background: $primary;
    color: $text;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: $accent;
    color: $text;
}
"""
    
    try:
        with open(css_file, 'w') as f:
            f.write(default_css)
        print(f"   ✅ Created default CSS file")
    except Exception as e:
        print(f"   ⚠️ Could not create CSS file: {e}")

def main():
    """Entry point principale del launcher."""
    print("=" * 70)
    print("🚀 EDC EXPLORER - TERMINAL UI LAUNCHER (FIXED)")
    print("=" * 70)
    print("Developed for Lorenzo - Principal Data Architect @ NTT Data Italia")
    print("Enterprise Data Catalog & AI Analytics Interface")
    print("=" * 70)
    
    # 1. Rileva struttura progetto
    project_root, has_real_modules = detect_project_structure()
    
    # 2. Controlla dipendenze
    if not check_dependencies():
        print("\n❌ Critical dependencies missing - cannot start!")
        sys.exit(1)
    
    # 3. Controlla terminale
    check_terminal_capabilities()
    
    # 4. Setup ambiente
    setup_environment(project_root, has_real_modules)
    
    # 5. Crea CSS se necessario
    create_css_if_missing()
    
    # 6. Import e avvio
    print("\n" + "=" * 70)
    print("🎯 All checks completed - Starting EDC Explorer...")
    
    if has_real_modules:
        print("🔗 LIVE MODE: Real EDC modules available")
    else:
        print("🎭 MOCK MODE: Using simulated data (no real EDC modules)")
    
    print("=" * 70)
    print("\n💡 Interface Tips:")
    print("   • Tab/Shift+Tab: Navigate between tabs")
    print("   • Arrow keys: Move between widgets")
    print("   • Enter/Space: Activate buttons")
    print("   • Ctrl+C: Exit application")
    print("   • Resize terminal for optimal experience (120x40+)")
    
    if not has_real_modules:
        print("\n🎭 Mock Mode Features:")
        print("   • All UI functionality works normally")
        print("   • Simulated EDC data and responses")
        print("   • Perfect for testing and demo")
        print("   • No real EDC/LLM connections required")
    
    print("\n" + "=" * 70)
    print("🚀 Launching application...")
    print("=" * 70)
    
    try:
        # Import dell'applicazione (ora con path corretto)
        from edc_explorer_tui import EDCExplorerApp
        
        app = EDCExplorerApp()
        app.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\n🔍 Troubleshooting:")
        print("   1. Make sure edc_explorer_tui.py is in the current directory")
        print("   2. Check that all Python modules are accessible")
        print("   3. Try running: python edc_explorer_tui.py directly")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()