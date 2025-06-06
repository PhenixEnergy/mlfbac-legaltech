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
    
    # Debug: Liste verfügbare Module auf
    core_path = os.path.join(current_dir, 'core')
    if os.path.exists(core_path):
        print(f"Core-Verzeichnis gefunden: {core_path}")
        for root, dirs, files in os.walk(core_path):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    rel_path = os.path.relpath(os.path.join(root, file), core_path)
                    print(f"  Verfügbares Modul: {rel_path}")
    
    print("Stellen Sie sicher, dass alle Abhängigkeiten installiert sind: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Allgemeiner Fehler beim Laden der Module: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

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
    logger = setup_logging(args.log_level)
    logger.info(f"🔄 Konvertiere {args.input} -> {args.output}")
    
    try:
        converter = JSONLConverter()
        success = converter.convert_file(args.input, args.output)
        
        if success:
            logger.info("✅ Konvertierung erfolgreich abgeschlossen")
            return 0
        else:
            logger.error("❌ Konvertierung fehlgeschlagen")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fehler bei Konvertierung: {e}")
        return 1

def segment_command(args) -> int:
    """Textsegmentierung"""
    logger = setup_logging(args.log_level)
    logger.info(f"✂️ Segmentiere {args.input} mit Strategie '{args.strategy}'")
    
    try:
        if args.strategy == "enhanced":
            engine = EnhancedSegmentationEngine()
            # Implementierung für enhanced segmentation
            logger.info("🔧 Enhanced Segmentierung wird ausgeführt...")
            # TODO: Implementiere enhanced segmentation call
            
        elif args.strategy == "semantic":
            logger.info("🧠 Semantische Segmentierung wird ausgeführt...")
            # TODO: Implementiere semantic segmentation call
            
        elif args.strategy == "training":
            logger.info("📚 Training-Segmentierung wird ausgeführt...")
            # Call existing segment_and_prepare_training_data
            sys.argv = ['segment_and_prepare_training_data.py', args.input, args.output]
            return segment_main()
            
        else:
            logger.error(f"❌ Unbekannte Segmentierungsstrategie: {args.strategy}")
            return 1
            
        logger.info("✅ Segmentierung erfolgreich abgeschlossen")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Segmentierung: {e}")
        return 1

def rag_prepare_command(args) -> int:
    """RAG-Datenvorbereitung"""
    logger = setup_logging(args.log_level)
    logger.info(f"🧠 Bereite RAG-Daten vor: {args.input} -> {args.output}")
    
    try:
        # Use fixed RAG preparation script
        sys.argv = ['prepare_rag_training_data_fixed.py', args.input, args.output]
        return rag_main()
        
    except Exception as e:
        logger.error(f"❌ Fehler bei RAG-Vorbereitung: {e}")
        return 1

def fine_tune_prepare_command(args) -> int:
    """Fine-Tuning Datenvorbereitung"""
    logger = setup_logging(args.log_level)
    logger.info(f"🎯 Bereite Fine-Tuning Daten vor: {args.input} -> {args.output}")
    
    try:
        integrator = OptimizedPipelineIntegrator()
        results = integrator.create_enhanced_fine_tuning_dataset([args.input], args.output)
        
        if results.get("success", False):
            logger.info("✅ Fine-Tuning Vorbereitung erfolgreich abgeschlossen")
            return 0
        else:
            logger.error("❌ Fine-Tuning Vorbereitung fehlgeschlagen")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fehler bei Fine-Tuning Vorbereitung: {e}")
        return 1

def validate_command(args) -> int:
    """Qualitätsvalidierung"""
    logger = setup_logging(args.log_level)
    logger.info(f"🔍 Validiere Datenqualität: {args.input}")
    
    try:
        sys.argv = ['enhanced_quality_validation.py', args.input]
        return validate_main()
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Validierung: {e}")
        return 1

def orchestrate_command(args) -> int:
    """Complete Pipeline-Orchestrierung"""
    logger = setup_logging(args.log_level)
    logger.info(f"🚀 Starte Pipeline-Orchestrierung: {args.input}")
    
    try:
        orchestrator = AdvancedPipelineOrchestrator(args.config)
        result = orchestrator.process_complete_pipeline(
            args.input,
            args.output_modes or ['fine_tuning'],
            args.optimization or 'standard'
        )
        
        if result.success:
            logger.info("✅ Pipeline-Orchestrierung erfolgreich abgeschlossen")
            return 0
        else:
            logger.error(f"❌ Pipeline-Orchestrierung fehlgeschlagen: {result.error}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fehler bei Pipeline-Orchestrierung: {e}")
        return 1

def optimize_command(args) -> int:
    """Optimierte Integration"""
    logger = setup_logging(args.log_level)
    logger.info(f"⚡ Starte optimierte Integration: {args.input}")
    
    try:
        integrator = OptimizedPipelineIntegrator()
        
        if args.mode == "segmentation":
            results = integrator.integrate_with_existing_segmentation(args.input, args.output)
        elif args.mode == "rag":
            results = integrator.optimize_rag_training_data(args.input, args.output)
        else:
            logger.error(f"❌ Unbekannter Optimierungsmodus: {args.mode}")
            return 1
            
        if results.get("success", False):
            logger.info("✅ Optimierte Integration erfolgreich abgeschlossen")
            return 0
        else:
            logger.error("❌ Optimierte Integration fehlgeschlagen")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fehler bei optimierter Integration: {e}")
        return 1

def main():
    """Hauptfunktion mit CLI-Interface"""
    parser = argparse.ArgumentParser(
        description="LegalTech NLP Pipeline - Unified Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Dokumentenkonvertierung
  python main.py convert --input data.json --output data.jsonl
  
  # Textsegmentierung
  python main.py segment --input data.jsonl --output segments.jsonl --strategy enhanced
  
  # RAG-Datenvorbereitung
  python main.py rag-prepare --input segments.jsonl --output rag_data.jsonl
  
  # Complete Pipeline-Orchestrierung
  python main.py orchestrate --input data.jsonl --output-modes fine_tuning rag_training
  
  # Optimierte Integration
  python main.py optimize --input data.jsonl --output optimized.jsonl --mode segmentation
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
        choices=["segmentation", "rag"],
        required=True,
        help="Optimierungsmodus"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Header
    print("🚀 LegalTech NLP Pipeline - Unified Entry Point")
    print("=" * 60)
    
    # Route to appropriate command
    command_map = {
        "convert": convert_command,
        "segment": segment_command,
        "rag-prepare": rag_prepare_command,
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
        print(f"\n❌ Unerwarteter Fehler: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())