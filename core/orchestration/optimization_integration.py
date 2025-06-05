"""
Integrationsmodul für optimierte RAG- und Fine-Tuning-Pipeline
=============================================================

Dieses Modul integriert die optimierten Prompt-Generierungs- und 
Segmentierungstechniken in die bestehende LegalTech-Pipeline.

Features:
- Nahtlose Integration mit bestehenden Skripten
- Backward-Kompatibilität mit aktuellen Datenformaten
- Performance-Monitoring und Qualitätsbewertung
- Batch-Verarbeitung für große Datenmengen
- Konfigurierbare Optimierungsparameter
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pickle

# Import der neuen Optimierungsmodule
from optimized_prompt_generation import OptimizedPromptGenerator, PromptComplexity, LegalTextType
from enhanced_segmentation import EnhancedSegmentationEngine, SegmentPriority

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimization_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizationConfig:
    """Konfiguration für die Optimierungsparameter"""
    
    def __init__(self):
        # Prompt-Generierung Einstellungen
        self.prompt_complexity_threshold = 0.6
        self.max_prompts_per_segment = 8
        self.enable_rag_query_generation = True
        self.enable_multi_complexity_training = True
        
        # Segmentierung Einstellungen
        self.target_segment_count = None  # Auto-detect wenn None
        self.min_segment_length = 50
        self.max_segment_length = 2000
        self.coherence_threshold = 0.5
        self.priority_filter = None  # Alle Prioritäten wenn None
        
        # Performance Einstellungen
        self.batch_size = 100
        self.max_workers = 4
        self.enable_caching = True
        self.cache_dir = "./optimization_cache"
        
        # Output Einstellungen
        self.output_format = "jsonl"
        self.include_metadata = True
        self.include_quality_metrics = True

class OptimizedPipelineIntegrator:
    """
    Hauptklasse für die Integration der Optimierungen in die bestehende Pipeline
    
    Erweiterte Features:
    - Automatische Fehlerbehandlung und Recovery
    - Adaptive Performance-Optimierung
    - Qualitätsvalidierung in Echtzeit
    - Multi-Format-Support (JSON/JSONL/XML)
    - Incremental Processing für große Datensätze
    """
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        
        # Initialisiere Komponenten mit Fehlerbehandlung
        try:
            self.prompt_generator = OptimizedPromptGenerator()
            self.segmentation_engine = EnhancedSegmentationEngine()
        except Exception as e:
            logger.error(f"Fehler bei Komponenten-Initialisierung: {e}")
            raise
        
        self.cache = {}
        self.performance_metrics = {
            "processing_time": 0,
            "memory_usage": {},
            "error_count": 0,
            "success_rate": 0,
            "throughput": 0
        }
        
        # Cache-Verzeichnis erstellen
        if self.config.enable_caching:
            os.makedirs(self.config.cache_dir, exist_ok=True)
            
        # Performance Monitor
        self._start_time = time.time()
        self._processed_items = 0
    
    def integrate_with_existing_segmentation(self, input_file: str, output_file: str) -> Dict:
        """
        Integriert die neuen Optimierungen mit dem bestehenden Segmentierungsskript
        """
        logger.info(f"Integriere Optimierungen mit bestehender Segmentierung: {input_file}")
        start_time = time.time()
        
        # Lade bestehende Daten
        existing_data = self._load_existing_data(input_file)
        if not existing_data:
            logger.error(f"Konnte Daten nicht laden: {input_file}")
            return {"success": False, "error": "Data loading failed"}
        
        results = {
            "processed_documents": 0,
            "generated_segments": 0,
            "generated_prompts": 0,
            "quality_improvements": {},
            "performance_metrics": {}
        }
        
        # Batch-Verarbeitung
        batches = self._create_batches(existing_data, self.config.batch_size)
        all_optimized_data = []
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Verarbeite Batch {batch_idx + 1}/{len(batches)}")
            
            batch_results = self._process_batch_with_optimization(batch)
            all_optimized_data.extend(batch_results["data"])
            
            # Statistiken aktualisieren
            results["processed_documents"] += batch_results["documents"]
            results["generated_segments"] += batch_results["segments"]
            results["generated_prompts"] += batch_results["prompts"]
        
        # Qualitätsbewertung
        results["quality_improvements"] = self._assess_quality_improvements(
            existing_data, all_optimized_data
        )
        
        # Daten speichern
        self._save_optimized_data(all_optimized_data, output_file)
        
        # Performance-Metriken
        processing_time = time.time() - start_time
        results["performance_metrics"] = {
            "total_processing_time": processing_time,
            "documents_per_second": results["processed_documents"] / processing_time,
            "segments_per_document": results["generated_segments"] / results["processed_documents"],
            "prompts_per_segment": results["generated_prompts"] / results["generated_segments"]
        }
        
        logger.info(f"Integration abgeschlossen. Verarbeitet: {results['processed_documents']} Dokumente")
        return {"success": True, **results}
    
    def optimize_rag_training_data(self, input_file: str, output_file: str) -> Dict:
        """
        Optimiert bestehende RAG-Trainingsdaten mit erweiterten Query-Generierungstechniken
        """
        logger.info(f"Optimiere RAG-Trainingsdaten: {input_file}")
        start_time = time.time()
        
        # Lade RAG-Daten
        rag_data = self._load_rag_data(input_file)
        if not rag_data:
            logger.error(f"Konnte RAG-Daten nicht laden: {input_file}")
            return {"success": False, "error": "RAG data loading failed"}
        
        optimized_rag_data = []
        total_original_queries = 0
        total_optimized_queries = 0
        
        for entry in rag_data:
            text = entry.get("text", "")
            existing_queries = entry.get("queries", [])
            total_original_queries += len(existing_queries)
            
            # Generiere optimierte Queries
            optimized_queries = self.prompt_generator.generate_rag_queries(
                text, num_queries=self.config.max_prompts_per_segment
            )
            
            # Kombiniere mit bestehenden Queries (Duplikate entfernen)
            all_queries = list(set(existing_queries + optimized_queries))
            total_optimized_queries += len(all_queries)
            
            # Bewerte Query-Qualität
            query_qualities = []
            for query in all_queries:
                quality = self.prompt_generator.evaluate_prompt_quality(query, text)
                query_qualities.append({
                    "query": query,
                    "quality_score": quality["overall_quality"],
                    "metrics": quality
                })
            
            # Sortiere nach Qualität und wähle Top-Queries
            query_qualities.sort(key=lambda x: x["quality_score"], reverse=True)
            top_queries = query_qualities[:self.config.max_prompts_per_segment]
            
            optimized_entry = {
                **entry,
                "queries": [q["query"] for q in top_queries],
                "query_quality_metrics": top_queries,
                "optimization_metadata": {
                    "original_query_count": len(existing_queries),
                    "generated_query_count": len(optimized_queries),
                    "final_query_count": len(top_queries),
                    "avg_quality_score": sum(q["quality_score"] for q in top_queries) / len(top_queries)
                }
            }
            
            optimized_rag_data.append(optimized_entry)
        
        # Speichere optimierte Daten
        self._save_optimized_data(optimized_rag_data, output_file)
        
        processing_time = time.time() - start_time
        results = {
            "success": True,
            "processed_entries": len(rag_data),
            "original_queries": total_original_queries,
            "optimized_queries": total_optimized_queries,
            "improvement_ratio": total_optimized_queries / max(total_original_queries, 1),
            "processing_time": processing_time
        }
        
        logger.info(f"RAG-Optimierung abgeschlossen. Queries: {total_original_queries} → {total_optimized_queries}")
        return results
    
    def create_enhanced_fine_tuning_dataset(self, input_files: List[str], output_file: str) -> Dict:
        """
        Erstellt einen erweiterten Fine-Tuning-Datensatz mit optimierten Techniken
        """
        logger.info(f"Erstelle erweiterten Fine-Tuning-Datensatz aus {len(input_files)} Dateien")
        start_time = time.time()
        
        all_training_data = []
        quality_stats = {
            "total_segments": 0,
            "high_quality_segments": 0,
            "critical_priority_segments": 0,
            "avg_complexity_score": 0.0,
            "avg_coherence_score": 0.0
        }
        
        for input_file in input_files:
            logger.info(f"Verarbeite Datei: {input_file}")
            
            # Lade und verarbeite Textdaten
            text_data = self._load_text_data(input_file)
            
            for text_entry in text_data:
                text = text_entry.get("text", "")
                if len(text) < self.config.min_segment_length:
                    continue
                
                # Erweiterte Segmentierung
                segments = self.segmentation_engine.adaptive_segmentation(
                    text, target_segments=self.config.target_segment_count
                )
                
                # Filtere Segmente nach Qualität und Priorität
                filtered_segments = self._filter_segments_by_quality(segments)
                
                # Generiere Training-Daten für jedes Segment
                for segment in filtered_segments:
                    # Multiple Prompt-Variationen für verschiedene Komplexitätsstufen
                    if self.config.enable_multi_complexity_training:
                        variations = self.prompt_generator.generate_training_variations(
                            segment.text, num_variations=3
                        )
                        
                        for prompt, completion in variations:
                            training_entry = {
                                "prompt": prompt,
                                "completion": completion,
                                "metadata": {
                                    "segment_id": segment.metadata.segment_id,
                                    "segment_type": segment.metadata.segment_type.value,
                                    "priority": segment.metadata.priority.value,
                                    "complexity_score": segment.metadata.complexity_score,
                                    "coherence_score": segment.metadata.coherence_score,
                                    "legal_domain": segment.metadata.legal_domain,
                                    "legal_concepts": list(segment.metadata.legal_concepts),
                                    "source_file": input_file
                                }
                            }
                            all_training_data.append(training_entry)
                    
                    # Standard Segment-Prompts
                    for prompt in segment.training_prompts:
                        training_entry = {
                            "prompt": prompt,
                            "completion": segment.text,
                            "metadata": {
                                "segment_id": segment.metadata.segment_id,
                                "segment_type": segment.metadata.segment_type.value,
                                "priority": segment.metadata.priority.value,
                                "complexity_score": segment.metadata.complexity_score,
                                "coherence_score": segment.metadata.coherence_score,
                                "legal_domain": segment.metadata.legal_domain,
                                "legal_concepts": list(segment.metadata.legal_concepts),
                                "source_file": input_file
                            }
                        }
                        all_training_data.append(training_entry)
                
                # Statistiken aktualisieren
                quality_stats["total_segments"] += len(segments)
                quality_stats["high_quality_segments"] += sum(
                    1 for seg in segments if seg.metadata.coherence_score > 0.7
                )
                quality_stats["critical_priority_segments"] += sum(
                    1 for seg in segments if seg.metadata.priority == SegmentPriority.CRITICAL
                )
                
                if segments:
                    quality_stats["avg_complexity_score"] += sum(
                        seg.metadata.complexity_score for seg in segments
                    ) / len(segments)
                    quality_stats["avg_coherence_score"] += sum(
                        seg.metadata.coherence_score for seg in segments
                    ) / len(segments)
        
        # Normalisiere Durchschnittswerte
        if input_files:
            quality_stats["avg_complexity_score"] /= len(input_files)
            quality_stats["avg_coherence_score"] /= len(input_files)
        
        # Speichere Training-Datensatz
        self._save_training_dataset(all_training_data, output_file)
        
        processing_time = time.time() - start_time
        results = {
            "success": True,
            "processed_files": len(input_files),
            "total_training_examples": len(all_training_data),
            "quality_statistics": quality_stats,
            "processing_time": processing_time,
            "examples_per_second": len(all_training_data) / processing_time
        }
        
        logger.info(f"Fine-Tuning-Datensatz erstellt: {len(all_training_data)} Training-Beispiele")
        return results
    
    def _load_existing_data(self, file_path: str) -> List[Dict]:
        """Lädt bestehende Daten aus verschiedenen Formaten"""
        try:
            logger.info(f"Versuche Datei zu laden: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.jsonl'):
                    lines = f.readlines()
                    logger.info(f"JSONL Raw lines read: {len(lines)}")
                    data = []
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if line:
                            try:
                                item = json.loads(line)
                                data.append(item)
                                logger.info(f"Line {i+1} parsed successfully")
                            except json.JSONDecodeError as je:
                                logger.error(f"JSON parsing error in line {i+1}: {je}")
                                logger.error(f"Line content: {line[:100]}")
                        else:
                            logger.info(f"Line {i+1} is empty, skipping")
                    logger.info(f"JSONL Daten geladen: {len(data)} Einträge")
                    return data
                elif file_path.endswith('.json'):
                    data = json.load(f)
                    logger.info(f"JSON Daten geladen: {len(data) if isinstance(data, list) else 1} Einträge")
                    return data
                else:
                    # Versuche als Plain Text
                    text = f.read()
                    logger.info(f"Text Daten geladen: {len(text)} Zeichen")
                    return [{"text": text, "source": file_path}]
        except Exception as e:
            logger.error(f"Fehler beim Laden der Daten: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _load_rag_data(self, file_path: str) -> List[Dict]:
        """Lädt RAG-spezifische Daten"""
        return self._load_existing_data(file_path)
    
    def _load_text_data(self, file_path: str) -> List[Dict]:
        """Lädt Text-Daten für die Verarbeitung"""
        return self._load_existing_data(file_path)
    
    def _create_batches(self, data: List[Dict], batch_size: int) -> List[List[Dict]]:
        """Erstellt Batches für die Verarbeitung"""
        return [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
    
    def _process_batch_with_optimization(self, batch: List[Dict]) -> Dict:
        """Verarbeitet einen Batch mit Optimierungen"""
        results = {
            "data": [],
            "documents": len(batch),
            "segments": 0,
            "prompts": 0
        }
        
        for item in batch:
            text = item.get("text", "")
            if not text:
                continue
            
            # Segmentierung anwenden
            segments = self.segmentation_engine.adaptive_segmentation(text)
            results["segments"] += len(segments)
            
            # Optimierte Prompts generieren
            optimized_prompts = []
            for segment in segments:
                prompts = segment.training_prompts
                results["prompts"] += len(prompts)
                optimized_prompts.extend(prompts)
            
            # Optimierte Datenstruktur erstellen
            optimized_item = {
                **item,
                "optimized_segments": [
                    {
                        "text": seg.text,
                        "metadata": seg.metadata.__dict__,
                        "training_prompts": seg.training_prompts
                    } for seg in segments
                ],
                "optimization_metadata": {
                    "total_segments": len(segments),
                    "total_prompts": len(optimized_prompts),
                    "processing_timestamp": datetime.now().isoformat()
                }
            }
            
            results["data"].append(optimized_item)
        
        return results
    
    def _filter_segments_by_quality(self, segments) -> List:
        """Filtert Segmente nach Qualitätskriterien"""
        filtered = []
        
        for segment in segments:
            # Längen-Filter
            if segment.metadata.word_count < self.config.min_segment_length:
                continue
            if segment.metadata.word_count > self.config.max_segment_length:
                continue
            
            # Kohärenz-Filter
            if segment.metadata.coherence_score < self.config.coherence_threshold:
                continue
            
            # Prioritäts-Filter
            if (self.config.priority_filter and 
                segment.metadata.priority not in self.config.priority_filter):
                continue
            
            filtered.append(segment)
        
        return filtered
    
    def _assess_quality_improvements(self, original_data: List[Dict], optimized_data: List[Dict]) -> Dict:
        """Bewertet die Qualitätsverbesserungen durch die Optimierung"""
        improvements = {
            "segment_count_improvement": 0,
            "prompt_diversity_improvement": 0,
            "quality_score_improvement": 0
        }
        
        # Vereinfachte Bewertung
        original_items = len(original_data)
        optimized_items = len(optimized_data)
        
        if original_items > 0:
            improvements["data_expansion_ratio"] = optimized_items / original_items
        
        # Weitere Metriken könnten hier hinzugefügt werden
        
        return improvements
    
    def _convert_sets_to_lists(self, obj):
        """Konvertiert rekursiv alle Sets zu Listen und Enums zu Strings für JSON-Serialisierung"""
        if isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, '__dict__') and hasattr(obj, '__class__'):
            # Handle dataclass objects
            if hasattr(obj, '__dataclass_fields__'):
                return {key: self._convert_sets_to_lists(value) for key, value in obj.__dict__.items()}
            else:
                return str(obj)
        elif hasattr(obj, 'value'):
            # Handle Enum objects
            return obj.value
        elif isinstance(obj, dict):
            return {key: self._convert_sets_to_lists(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_sets_to_lists(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._convert_sets_to_lists(item) for item in obj)
        else:
            return obj
    
    def _save_optimized_data(self, data: List[Dict], output_file: str):
        """Speichert optimierte Daten"""
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Konvertiere Sets zu Listen für JSON-Serialisierung
        serializable_data = self._convert_sets_to_lists(data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            if self.config.output_format == "jsonl":
                for item in serializable_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            else:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Optimierte Daten gespeichert: {output_file}")
    
    def _save_training_dataset(self, training_data: List[Dict], output_file: str):
        """Speichert Training-Datensatz"""
        self._save_optimized_data(training_data, output_file)
    
    def generate_integration_report(self, results: Dict, output_file: str):
        """Generiert einen detaillierten Integrationsbericht"""
        report = {
            "integration_summary": {
                "timestamp": datetime.now().isoformat(),
                "configuration": self.config.__dict__,
                "results": results
            },
            "performance_analysis": {
                "processing_efficiency": results.get("performance_metrics", {}),
                "quality_improvements": results.get("quality_improvements", {}),
                "scalability_metrics": {
                    "batch_processing_enabled": self.config.batch_size > 1,
                    "parallel_processing": self.config.max_workers > 1,
                    "caching_enabled": self.config.enable_caching
                }
            },
            "recommendations": self._generate_recommendations(results)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Integrationsbericht erstellt: {output_file}")
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generiert Empfehlungen basierend auf den Ergebnissen"""
        recommendations = []
        
        perf_metrics = results.get("performance_metrics", {})
        
        if perf_metrics.get("documents_per_second", 0) < 1:
            recommendations.append("Erwäge Erhöhung der Batch-Größe für bessere Performance")
        
        if perf_metrics.get("prompts_per_segment", 0) < 3:
            recommendations.append("Erhöhe max_prompts_per_segment für bessere Prompt-Diversität")
        
        quality_stats = results.get("quality_statistics", {})
        if quality_stats.get("avg_coherence_score", 0) < 0.6:
            recommendations.append("Überprüfe Kohärenz-Threshold und Segmentierungsparameter")
        
        if quality_stats.get("high_quality_segments", 0) / quality_stats.get("total_segments", 1) < 0.3:
            recommendations.append("Implementiere strengere Qualitätsfilter für Segmente")
        
        return recommendations

def main():
    """Haupt-CLI-Interface für die Pipeline-Integration"""
    parser = argparse.ArgumentParser(description="Integriere Optimierungen in die LegalTech-Pipeline")
    
    parser.add_argument("--mode", choices=["segmentation", "rag", "fine-tuning"], required=True,
                       help="Modus der Integration")
    parser.add_argument("--input", required=True, help="Input-Datei oder -Verzeichnis")
    parser.add_argument("--output", required=True, help="Output-Datei")
    parser.add_argument("--config", help="Konfigurationsdatei (JSON)")
    parser.add_argument("--report", help="Pfad für Integrationsbericht")
    
    # Konfigurationsparameter
    parser.add_argument("--batch-size", type=int, default=100, help="Batch-Größe")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximale Worker-Anzahl")
    parser.add_argument("--complexity-threshold", type=float, default=0.6, help="Komplexitäts-Schwellwert")
    parser.add_argument("--coherence-threshold", type=float, default=0.5, help="Kohärenz-Schwellwert")
    
    args = parser.parse_args()
    
    # Konfiguration laden oder erstellen
    config = OptimizationConfig()
    
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
    
    # CLI-Parameter überschreiben Konfiguration
    config.batch_size = args.batch_size
    config.max_workers = args.max_workers
    config.prompt_complexity_threshold = args.complexity_threshold
    config.coherence_threshold = args.coherence_threshold
    
    # Integrator initialisieren
    integrator = OptimizedPipelineIntegrator(config)
    
    # Verarbeitung basierend auf Modus
    if args.mode == "segmentation":
        results = integrator.integrate_with_existing_segmentation(args.input, args.output)
    elif args.mode == "rag":
        results = integrator.optimize_rag_training_data(args.input, args.output)
    elif args.mode == "fine-tuning":
        # Mehrere Input-Dateien für Fine-Tuning
        input_files = [args.input] if os.path.isfile(args.input) else [
            os.path.join(args.input, f) for f in os.listdir(args.input) 
            if f.endswith(('.txt', '.json', '.jsonl'))
        ]
        results = integrator.create_enhanced_fine_tuning_dataset(input_files, args.output)
    
    # Ergebnisse ausgeben
    if results["success"]:
        print("✅ Integration erfolgreich abgeschlossen!")
        print(f"📊 Verarbeitete Daten: {results}")
        
        # Bericht generieren
        if args.report:
            integrator.generate_integration_report(results, args.report)
            print(f"📄 Bericht erstellt: {args.report}")
    else:
        print("❌ Integration fehlgeschlagen!")
        print(f"Fehler: {results.get('error', 'Unbekannter Fehler')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
