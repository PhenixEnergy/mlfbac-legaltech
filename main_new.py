#!/usr/bin/env python3
"""
LegalTech NLP Pipeline - Unified Entry Point
===========================================

Zentraler Einstiegspunkt für alle Pipeline-Funktionen:
- Dokumentenkonvertierung
- Textsegmentierung  
- RAG-Datenvorbereitung
- Fine-Tuning Vorbereitung
- Qualitätsvalidierung
- Pipeline-Orchestrierung

Version: 1.0
Erstellt: Juni 2025
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Core module script paths
SCRIPT_PATHS = {
    'convert': os.path.join(current_dir, 'core', 'conversion', 'jsonl_converter.py'),
    'segment': os.path.join(current_dir, 'core', 'segmentation', 'enhanced_segmentation.py'),
    'segment_training': os.path.join(current_dir, 'core', 'segmentation', 'segment_and_prepare_training_data.py'),
    'rag': os.path.join(current_dir, 'core', 'rag', 'prepare_rag_training_data_fixed.py'),
    'rag_legacy': os.path.join(current_dir, 'core', 'rag', 'prepare_rag_training_data.py'),
    'prompt_gen': os.path.join(current_dir, 'core', 'rag', 'optimized_prompt_generation.py'),
    'validate': os.path.join(current_dir, 'core', 'validation', 'enhanced_quality_validation.py'),
    'orchestrate': os.path.join(current_dir, 'core', 'orchestration', 'advanced_pipeline_orchestrator.py'),
    'optimize': os.path.join(current_dir, 'core', 'orchestration', 'optimization_integration.py')
}

def run_script(script_path: str, args: List[str] = None) -> int:
    """
    Execute a Python script as subprocess
    
    Args:
        script_path: Path to the Python script
        args: Additional arguments to pass to the script
        
    Returns:
        Exit code from the subprocess
    """
    if not os.path.exists(script_path):
        logger.error(f"❌ Script nicht gefunden: {script_path}")
        return 1
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    try:
        logger.info(f"🔄 Führe aus: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode
    except Exception as e:
        logger.error(f"❌ Fehler beim Ausführen von {script_path}: {e}")
        return 1

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Konfiguriert Logging für die Pipeline"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('legaltech_pipeline.log')
        ]
    )
    return logging.getLogger('LegalTechPipeline')

def convert_command(args) -> int:
    """Dokumentenkonvertierung"""
    logger.info(f"🔄 Konvertiere {args.input} -> {args.output}")
    
    script_args = []
    if hasattr(args, 'input') and args.input:
        script_args.extend(['--input', args.input])
    if hasattr(args, 'output') and args.output:
        script_args.extend(['--output', args.output])
    
    return run_script(SCRIPT_PATHS['convert'], script_args)

def segment_command(args) -> int:
    """Textsegmentierung"""
    logger.info(f"✂️ Segmentiere {args.input} mit Strategie '{args.strategy}'")
    
    script_args = []
    if hasattr(args, 'input') and args.input:
        script_args.extend(['--input', args.input])
    if hasattr(args, 'output') and args.output:
        script_args.extend(['--output', args.output])
    
    if args.strategy == "training":
        # Use segment_and_prepare_training_data.py for training strategy
        return run_script(SCRIPT_PATHS['segment_training'], script_args)
    else:
        # Use enhanced_segmentation.py for other strategies
        if hasattr(args, 'strategy') and args.strategy:
            script_args.extend(['--strategy', args.strategy])
        return run_script(SCRIPT_PATHS['segment'], script_args)

def rag_prepare_command(args) -> int:
    """RAG-Datenvorbereitung"""
    logger.info(f"🧠 Bereite RAG-Daten vor: {args.input} -> {args.output}")
    
    script_args = []
    if hasattr(args, 'input') and args.input:
        script_args.extend(['--input', args.input])
    if hasattr(args, 'output') and args.output:
        script_args.extend(['--output', args.output])
    
    return run_script(SCRIPT_PATHS['rag'], script_args)

def fine_tune_prepare_command(args) -> int:
    """Fine-Tuning Datenvorbereitung"""
    logger.info(f"🎯 Bereite Fine-Tuning Daten vor: {args.input} -> {args.output}")
    
    script_args = []
    if hasattr(args, 'input') and args.input:
        script_args.extend(['--input', args.input])
    if hasattr(args, 'output') and args.output:
        script_args.extend(['--output', args.output])
    if hasattr(args, 'mode') and args.mode:
        script_args.extend(['--mode', 'fine_tuning'])
    
    return run_script(SCRIPT_PATHS['optimize'], script_args)

def validate_command(args) -> int:
    """Qualitätsvalidierung"""
    logger.info(f"🔍 Validiere Datenqualität: {args.input}")
    
    script_args = []
    if hasattr(args, 'input') and args.input:
        script_args.extend(['--input', args.input])
    
    return run_script(SCRIPT_PATHS['validate'], script_args)

def orchestrate_command(args) -> int:
    """Complete Pipeline-Orchestrierung"""
    logger.info(f"🚀 Starte Pipeline-Orchestrierung: {args.input}")
    
    script_args = []
    if hasattr(args, 'input') and args.input:
        script_args.extend(['--input', args.input])
    if hasattr(args, 'output_modes') and args.output_modes:
        script_args.extend(['--output-modes'] + args.output_modes)
    if hasattr(args, 'optimization') and args.optimization:
        script_args.extend(['--optimization', args.optimization])
    if hasattr(args, 'config') and args.config:
        script_args.extend(['--config', args.config])
    
    return run_script(SCRIPT_PATHS['orchestrate'], script_args)

def optimize_command(args) -> int:
    """Optimierte Integration"""
    logger.info(f"⚡ Starte optimierte Integration: {args.input}")
    
    script_args = []
    if hasattr(args, 'input') and args.input:
        script_args.extend(['--input', args.input])
    if hasattr(args, 'output') and args.output:
        script_args.extend(['--output', args.output])
    if hasattr(args, 'mode') and args.mode:
        script_args.extend(['--mode', args.mode])
    
    return run_script(SCRIPT_PATHS['optimize'], script_args)

def prompt_gen_command(args) -> int:
    """Optimierte Prompt-Generierung"""
    logger.info(f"🎯 Generiere optimierte Prompts: {args.input}")
    
    script_args = []
    if hasattr(args, 'input') and args.input:
        script_args.extend(['--input', args.input])
    if hasattr(args, 'output') and args.output:
        script_args.extend(['--output', args.output])
    
    return run_script(SCRIPT_PATHS['prompt_gen'], script_args)

def status_command(args) -> int:
    """Zeige Pipeline-Status"""
    logger.info("📊 Pipeline-Status")
    
    print("\n🔍 LegalTech NLP Pipeline - Status")
    print("=" * 50)
    
    # Check if all core scripts exist
    missing_scripts = []
    for name, path in SCRIPT_PATHS.items():
        if os.path.exists(path):
            print(f"✅ {name.ljust(15)}: {path}")
        else:
            print(f"❌ {name.ljust(15)}: {path} (FEHLT)")
            missing_scripts.append(name)
    
    print(f"\n📈 Status: {len(SCRIPT_PATHS) - len(missing_scripts)}/{len(SCRIPT_PATHS)} Module verfügbar")
    
    if missing_scripts:
        print(f"⚠️  Fehlende Module: {', '.join(missing_scripts)}")
        return 1
    else:
        print("✅ Alle Module verfügbar!")
        return 0

def main():
    """Hauptfunktion mit CLI-Interface"""
    parser = argparse.ArgumentParser(
        description="LegalTech NLP Pipeline - Unified Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Pipeline-Status anzeigen
  python main.py status
  
  # Dokumentenkonvertierung
  python main.py convert --input data.json --output data.jsonl
  
  # Textsegmentierung
  python main.py segment --input data.jsonl --output segments.jsonl --strategy enhanced
  
  # RAG-Datenvorbereitung
  python main.py rag-prepare --input segments.jsonl --output rag_data.jsonl
  
  # Prompt-Generierung
  python main.py prompt-gen --input data.jsonl --output prompts.jsonl
  
  # Complete Pipeline-Orchestrierung
  python main.py orchestrate --input data.jsonl --output-modes fine_tuning rag_training
  
  # Optimierte Integration
  python main.py optimize --input data.jsonl --output optimized.jsonl --mode segmentation
  
  # Qualitätsvalidierung
  python main.py validate --input data.jsonl
        """
    )
    
    # Global arguments
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging-Level (Standard: INFO)"
    )
    
    parser.add_argument(
        "--config",
        help="Pfad zur Konfigurationsdatei"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Verfügbare Kommandos")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Pipeline-Status anzeigen")
    
    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Dokumentenkonvertierung")
    convert_parser.add_argument("--input", required=True, help="Eingabedatei")
    convert_parser.add_argument("--output", required=True, help="Ausgabedatei")
    
    # Segment command
    segment_parser = subparsers.add_parser("segment", help="Textsegmentierung")
    segment_parser.add_argument("--input", required=True, help="Eingabedatei")
    segment_parser.add_argument("--output", required=True, help="Ausgabedatei")
    segment_parser.add_argument(
        "--strategy", 
        choices=["enhanced", "semantic", "training"],
        default="enhanced",
        help="Segmentierungsstrategie (Standard: enhanced)"
    )
    
    # RAG prepare command
    rag_parser = subparsers.add_parser("rag-prepare", help="RAG-Datenvorbereitung")
    rag_parser.add_argument("--input", required=True, help="Eingabedatei")
    rag_parser.add_argument("--output", required=True, help="Ausgabedatei")
    
    # Prompt generation command
    prompt_parser = subparsers.add_parser("prompt-gen", help="Optimierte Prompt-Generierung")
    prompt_parser.add_argument("--input", required=True, help="Eingabedatei")
    prompt_parser.add_argument("--output", required=True, help="Ausgabedatei")
    
    # Fine-tune prepare command
    ft_parser = subparsers.add_parser("fine-tune-prepare", help="Fine-Tuning Datenvorbereitung")
    ft_parser.add_argument("--input", required=True, help="Eingabedatei")
    ft_parser.add_argument("--output", required=True, help="Ausgabedatei")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Qualitätsvalidierung")
    validate_parser.add_argument("--input", required=True, help="Eingabedatei")
    
    # Orchestrate command (Enterprise Pipeline)
    orchestrate_parser = subparsers.add_parser("orchestrate", help="Complete Pipeline-Orchestrierung")
    orchestrate_parser.add_argument("--input", required=True, help="Eingabedatei")
    orchestrate_parser.add_argument(
        "--output-modes",
        nargs="+",
        choices=["fine_tuning", "rag_training", "rag_knowledge_base", "analysis_report"],
        help="Output-Modi"
    )
    orchestrate_parser.add_argument(
        "--optimization",
        choices=["basic", "standard", "advanced", "maximum"],
        help="Optimierungsstufe"
    )
    
    # Optimize command (Integration)
    optimize_parser = subparsers.add_parser("optimize", help="Optimierte Integration")
    optimize_parser.add_argument("--input", required=True, help="Eingabedatei")
    optimize_parser.add_argument("--output", required=True, help="Ausgabedatei")
    optimize_parser.add_argument(
        "--mode",
        choices=["segmentation", "rag", "fine_tuning"],
        required=True,
        help="Optimierungsmodus"
    )
    
    args = parser.parse_args()
    
    # Setup logging based on args
    setup_logging(args.log_level)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Header
    print("🚀 LegalTech NLP Pipeline - Unified Entry Point")
    print("=" * 60)
    
    # Route to appropriate command
    command_map = {
        "status": status_command,
        "convert": convert_command,
        "segment": segment_command,
        "rag-prepare": rag_prepare_command,
        "prompt-gen": prompt_gen_command,
        "fine-tune-prepare": fine_tune_prepare_command,
        "validate": validate_command,
        "orchestrate": orchestrate_command,
        "optimize": optimize_command
    }
    
    try:
        return command_map[args.command](args)
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline vom Benutzer unterbrochen")
        return 130
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler: {e}")
        print(f"\n❌ Unerwarteter Fehler: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
