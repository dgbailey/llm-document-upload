#!/usr/bin/env python3
"""
Simple demo runner for AI Document Summary System
"""
import subprocess
import sys
import time
import os
import signal

def run_command(cmd, cwd=None):
    """Run a command and return the process"""
    return subprocess.Popen(cmd, shell=True, cwd=cwd)

def main():
    print("🚀 Starting AI Document Summary Demo Mode...")
    print("")
    
    processes = []
    
    try:
        # Change to backend directory
        backend_dir = "backend"
        frontend_dir = "frontend"
        
        # Initialize database
        print("📊 Initializing database...")
        subprocess.run(
            "source venv/bin/activate && python -c 'from app.database import init_db; init_db()'",
            shell=True, cwd=backend_dir
        )
        
        # Start backend
        print("🔧 Starting Backend Server...")
        backend_process = run_command(
            "source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000",
            cwd=backend_dir
        )
        processes.append(backend_process)
        
        # Wait for backend to be ready
        time.sleep(3)
        
        # Start frontend
        print("🎨 Starting Frontend...")
        frontend_process = run_command(
            "npm run dev -- --host 0.0.0.0 --port 5173",
            cwd=frontend_dir
        )
        processes.append(frontend_process)
        
        # Wait a bit for everything to start
        time.sleep(3)
        
        print("\n✨ Demo Mode is running!\n")
        print("Access the application at:")
        print("  Frontend: http://localhost:5173")
        print("  Backend API: http://localhost:8000")
        print("  API Docs: http://localhost:8000/docs")
        print("\nDemo Features:")
        print("  • No API keys required")
        print("  • Simulated AI processing")
        print("  • Test with fake document uploads")
        print("  • View real-time statistics")
        print("\nPress Ctrl+C to stop all services\n")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping services...")
        for p in processes:
            p.terminate()
        print("✅ Demo stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()