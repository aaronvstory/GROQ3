#!/usr/bin/env python3
"""
Groq Whisperer Launcher
Simple launcher script for the Groq Whisperer application.
"""

import sys
import platform
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich import print as rp
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    print("Rich library not found. Please install requirements:")
    print("pip install -r requirements.txt")
    sys.exit(1)

def main():
    """Main launcher function with platform checks and error handling."""
    console = Console()
    
    # Platform compatibility check
    if platform.system().lower() != "windows":
        rp("[bold yellow]⚠️  Only Windows is fully supported. Good luck![/bold yellow]")
    
    # Check if the main application file exists
    main_script = Path(__file__).parent / "groq3new-Copy.py"
    if not main_script.exists():
        console.print(Panel(
            "[bold red]❌ Main application file not found![/bold red]\n"
            f"Expected: {main_script}\n"
            "Please ensure groq3new-Copy.py is in the same directory.",
            title="Launch Error",
            border_style="red"
        ))
        sys.exit(1)
    
    # Welcome message
    console.print(Panel(
        "[bold blue]🎙️ Groq Whisperer[/bold blue]\n"
        "Voice Transcription Application\n"
        "[dim]Starting application...[/dim]",
        title="Welcome",
        border_style="blue"
    ))
    
    try:
        # Import and run the main application
        import importlib.util
        spec = importlib.util.spec_from_file_location("groq_app", main_script)
        groq_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(groq_app)
        
        # Run the main function
        if hasattr(groq_app, 'main'):
            groq_app.main()
        else:
            console.print("[red]❌ Main function not found in application file[/red]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]🛑 Application interrupted by user[/yellow]")
    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ Application failed to start:[/bold red]\n"
            f"Error: {str(e)}\n\n"
            "[yellow]Common solutions:[/yellow]\n"
            "1. Ensure Python 3.8+ is installed\n"
            "2. Set GROQ_API_KEY environment variable\n"
            "3. Install requirements: pip install -r requirements.txt\n"
            "4. Check internet connection",
            title="Launch Error",
            border_style="red"
        ))
        sys.exit(1)

if __name__ == "__main__":
    main()
