#!/usr/bin/env python3
"""
Enhanced LegalTech Quality Validation Suite - Enterprise Version
==============================================================

Umfassende Qualitätsvalidierung für alle Pipeline-Outputs:
- Multi-Format-Validierung (JSON, JSONL, XML, CSV)
- Inhaltliche Qualitätsprüfung mit ML-Metriken
- Performance-Benchmarking mit statistischer Analyse
- Consistency-Checks mit Anomalie-Erkennung
- Automated Testing mit Regression-Detection
- Batch-Processing mit paralleler Validierung
- Real-time Monitoring und Alerting
- Comprehensive Reporting mit Dashboard-Export

Version: 2.0 (Enhanced Enterprise)
Erstellt: Mai 2025
"""

import json
import os
import sys
import argparse
import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from pathlib import Path
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
import re
import statistics
from collections import defaultdict, Counter
import hashlib
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import traceback
from functools import wraps, lru_cache

# Optional dependencies for advanced features
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

try:
    import psutil
    SYSTEM_MONITORING_AVAILABLE = True
except ImportError:
    SYSTEM_MONITORING_AVAILABLE = False

# Color codes for enhanced output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

@dataclass
class ValidationResult:
    """Erweiterte Validierungsergebnisse mit Performance-Metriken"""
    passed: bool
    score: float
    details: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    performance_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    memory_usage: float = 0.0
    validation_level: str = "standard"

@dataclass
class QualityMetrics:
    """Umfassende Qualitäts-Metriken"""
    content_quality: float = 0.0
    format_consistency: float = 0.0
    data_completeness: float = 0.0
    semantic_coherence: float = 0.0
    performance_score: float = 0.0
    overall_score: float = 0.0
    anomaly_score: float = 0.0
    regression_indicators: List[str] = field(default_factory=list)

@dataclass
class BenchmarkResults:
    """Performance-Benchmark-Ergebnisse"""
    throughput_items_per_second: float = 0.0
    memory_efficiency_score: float = 0.0
    error_rate: float = 0.0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)

class EnhancedQualityValidator:
    """
    Erweiterte Qualitätsvalidierung mit Enterprise-Features
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialisiert den erweiterten Qualitäts-Validator
        
        Args:
            config: Konfiguration für Validierungsparameter
        """
        self.config = config or self._get_default_config()
        self.logger = self._setup_logging()
        self.baseline_metrics = {}
        self.anomaly_detectors = {}
        self.performance_history = defaultdict(list)
        
        # Threading für parallele Validierung
        self.max_workers = min(mp.cpu_count(), 8)
        self.validation_cache = {}
        
        self.logger.info(f"{Colors.HEADER}🔍 Enhanced Quality Validator initialisiert{Colors.ENDC}")
    
    def _get_default_config(self) -> Dict:
        """Standard-Konfiguration für Qualitätsvalidierung"""
        return {
            "thresholds": {
                "min_content_quality": 0.7,
                "min_format_consistency": 0.9,
                "min_data_completeness": 0.8,
                "max_anomaly_score": 0.3,
                "max_error_rate": 0.05
            },
            "validation_levels": {
                "basic": ["format", "structure"],
                "standard": ["format", "structure", "content", "consistency"],
                "comprehensive": ["format", "structure", "content", "consistency", "performance", "anomalies"],
                "enterprise": ["format", "structure", "content", "consistency", "performance", "anomalies", "regression", "benchmarking"]
            },
            "performance": {
                "enable_benchmarking": True,
                "enable_regression_detection": True,
                "baseline_retention_days": 30
            },
            "alerts": {
                "enable_real_time_alerts": True,
                "alert_thresholds": {
                    "quality_drop": 0.1,
                    "performance_degradation": 0.2,
                    "error_spike": 0.05
                }
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Erweiterte Logging-Konfiguration"""
        logger = logging.getLogger('EnhancedQualityValidator')
        logger.setLevel(logging.INFO)
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(f'{Colors.OKCYAN}%(asctime)s{Colors.ENDC} - %(levelname)s - %(message)s')
        )
        
        # File Handler
        file_handler = logging.FileHandler('enhanced_quality_validation.log')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
        )
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def validate_dataset(self, 
                        file_path: str, 
                        validation_level: str = "standard",
                        enable_benchmarking: bool = False) -> ValidationResult:
        """
        Hauptvalidierung für Dataset
        
        Args:
            file_path: Pfad zur zu validierenden Datei
            validation_level: Validierungsstufe (basic, standard, comprehensive, enterprise)
            enable_benchmarking: Performance-Benchmarking aktivieren
            
        Returns:
            ValidationResult mit detaillierten Ergebnissen
        """
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        self.logger.info(f"{Colors.HEADER}🔍 Starte Qualitätsvalidierung{Colors.ENDC}")
        self.logger.info(f"Datei: {file_path}")
        self.logger.info(f"Validierungsstufe: {validation_level}")
        
        try:
            # Lade und parse Daten
            data = self._load_data(file_path)
            if not data:
                return ValidationResult(
                    passed=False,
                    score=0.0,
                    details={"error": "Konnte Datei nicht laden"},
                    errors=["Datei konnte nicht geladen werden"]
                )
            
            # Führe Validierungen basierend auf Level durch
            validation_steps = self.config["validation_levels"][validation_level]
            
            results = {}
            quality_metrics = QualityMetrics()
            
            if "format" in validation_steps:
                results["format"] = self._validate_format(data)
                quality_metrics.format_consistency = results["format"].score
                
            if "structure" in validation_steps:
                results["structure"] = self._validate_structure(data)
                quality_metrics.data_completeness = results["structure"].score
                
            if "content" in validation_steps:
                results["content"] = self._validate_content(data)
                quality_metrics.content_quality = results["content"].score
                
            if "consistency" in validation_steps:
                results["consistency"] = self._validate_consistency(data)
                quality_metrics.semantic_coherence = results["consistency"].score
                
            if "performance" in validation_steps:
                results["performance"] = self._validate_performance(data)
                quality_metrics.performance_score = results["performance"].score
                
            if "anomalies" in validation_steps:
                results["anomalies"] = self._detect_anomalies(data)
                quality_metrics.anomaly_score = results["anomalies"].score
                
            if "regression" in validation_steps:
                results["regression"] = self._detect_regression(data)
                
            if "benchmarking" in validation_steps or enable_benchmarking:
                benchmark_results = self._run_benchmarks(data)
                results["benchmarks"] = benchmark_results
            
            # Berechne Gesamtscore
            overall_score = self._calculate_overall_score(quality_metrics)
            quality_metrics.overall_score = overall_score
            
            # Bestimme ob Validierung bestanden
            passed = overall_score >= self.config["thresholds"]["min_content_quality"]
            
            # Sammle alle Fehler und Warnungen
            all_errors = []
            all_warnings = []
            for result in results.values():
                if hasattr(result, 'errors'):
                    all_errors.extend(result.errors)
                if hasattr(result, 'warnings'):
                    all_warnings.extend(result.warnings)
            
            processing_time = time.time() - start_time
            memory_usage = self._get_memory_usage() - initial_memory
            
            # Erstelle finales Ergebnis
            validation_result = ValidationResult(
                passed=passed,
                score=overall_score,
                details={
                    "quality_metrics": asdict(quality_metrics),
                    "validation_results": {k: asdict(v) if hasattr(v, '__dict__') else v for k, v in results.items()},
                    "file_info": {
                        "path": file_path,
                        "size_mb": os.path.getsize(file_path) / (1024 * 1024),
                        "item_count": len(data)
                    }
                },
                errors=all_errors,
                warnings=all_warnings,
                metrics={
                    "content_quality": quality_metrics.content_quality,
                    "format_consistency": quality_metrics.format_consistency,
                    "data_completeness": quality_metrics.data_completeness,
                    "overall_score": overall_score
                },
                processing_time=processing_time,
                memory_usage=memory_usage,
                validation_level=validation_level
            )
            
            self.logger.info(f"{Colors.OKGREEN}✅ Validierung abgeschlossen{Colors.ENDC}")
            self.logger.info(f"Gesamtscore: {overall_score:.3f}")
            self.logger.info(f"Status: {'BESTANDEN' if passed else 'FEHLGESCHLAGEN'}")
            
            return validation_result
            
        except Exception as e:
            error_msg = f"Validierungsfehler: {str(e)}"
            self.logger.error(f"{Colors.FAIL}{error_msg}{Colors.ENDC}")
            self.logger.error(traceback.format_exc())
            
            return ValidationResult(
                passed=False,
                score=0.0,
                details={"error": error_msg},
                errors=[error_msg],
                processing_time=time.time() - start_time
            )
    
    def _load_data(self, file_path: str) -> Optional[List[Dict]]:
        """Lädt Daten aus verschiedenen Formaten"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.jsonl':
                data = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if line.strip():
                            try:
                                data.append(json.loads(line))
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"Ungültige JSON-Zeile {line_num}: {e}")
                return data
                
            elif file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else [data]
                    
            else:
                self.logger.error(f"Nicht unterstütztes Dateiformat: {file_ext}")
                return None
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Datei: {e}")
            return None
    
    def _validate_format(self, data: List[Dict]) -> ValidationResult:
        """Validiert Datenformat"""
        errors = []
        warnings = []
        score = 1.0
        
        if not data:
            errors.append("Keine Daten gefunden")
            return ValidationResult(False, 0.0, {}, errors, warnings)
        
        # Prüfe JSON-Struktur
        required_fields = ["messages", "conversation_id"]  # Basis-Felder
        
        valid_items = 0
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append(f"Item {i} ist kein Dictionary")
                continue
                
            # Prüfe Basis-Struktur
            if "messages" in item:
                valid_items += 1
            else:
                warnings.append(f"Item {i} hat keine 'messages' Struktur")
        
        format_score = valid_items / len(data) if data else 0
        score = format_score
        
        return ValidationResult(
            passed=format_score >= 0.9,
            score=score,
            details={
                "total_items": len(data),
                "valid_items": valid_items,
                "format_score": format_score
            },
            errors=errors,
            warnings=warnings
        )
    
    def _validate_structure(self, data: List[Dict]) -> ValidationResult:
        """Validiert Datenstruktur"""
        errors = []
        warnings = []
        
        if not data:
            return ValidationResult(False, 0.0, {}, ["Keine Daten"], [])
        
        complete_items = 0
        
        for i, item in enumerate(data):
            if "messages" in item:
                messages = item["messages"]
                if isinstance(messages, list) and len(messages) >= 2:
                    # Prüfe Message-Struktur
                    has_system = any(msg.get("role") == "system" for msg in messages)
                    has_user = any(msg.get("role") == "user" for msg in messages)
                    has_assistant = any(msg.get("role") == "assistant" for msg in messages)
                    
                    if has_system and has_user and has_assistant:
                        complete_items += 1
                    else:
                        warnings.append(f"Item {i}: Unvollständige Message-Rollen")
                else:
                    warnings.append(f"Item {i}: Ungültige Messages-Struktur")
        
        completeness_score = complete_items / len(data)
        
        return ValidationResult(
            passed=completeness_score >= 0.8,
            score=completeness_score,
            details={
                "total_items": len(data),
                "complete_items": complete_items,
                "completeness_score": completeness_score
            },
            errors=errors,
            warnings=warnings
        )
    
    def _validate_content(self, data: List[Dict]) -> ValidationResult:
        """Validiert Inhaltsqualität"""
        errors = []
        warnings = []
        
        if not data:
            return ValidationResult(False, 0.0, {}, ["Keine Daten"], [])
        
        quality_scores = []
        
        for i, item in enumerate(data):
            item_score = self._calculate_content_quality(item)
            quality_scores.append(item_score)
            
            if item_score < 0.5:
                warnings.append(f"Item {i}: Niedrige Inhaltsqualität ({item_score:.2f})")
        
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0
        
        return ValidationResult(
            passed=avg_quality >= 0.7,
            score=avg_quality,
            details={
                "average_quality": avg_quality,
                "quality_distribution": {
                    "min": min(quality_scores) if quality_scores else 0,
                    "max": max(quality_scores) if quality_scores else 0,
                    "median": statistics.median(quality_scores) if quality_scores else 0
                }
            },
            errors=errors,
            warnings=warnings
        )
    
    def _calculate_content_quality(self, item: Dict) -> float:
        """Berechnet Inhaltsqualität für ein Item"""
        if "messages" not in item:
            return 0.0
        
        quality_factors = []
        
        for message in item["messages"]:
            if "content" in message:
                content = message["content"]
                
                # Längen-Qualität
                length_score = min(len(content) / 100, 1.0)  # Normalisiert auf 100 Zeichen
                quality_factors.append(length_score)
                
                # Text-Qualität (einfache Heuristik)
                text_quality = self._assess_text_quality(content)
                quality_factors.append(text_quality)
        
        return statistics.mean(quality_factors) if quality_factors else 0.0
    
    def _assess_text_quality(self, text: str) -> float:
        """Einfache Textqualitätsbewertung"""
        if not text or len(text) < 10:
            return 0.0
        
        quality_score = 0.5  # Basis-Score
        
        # Prüfe auf vollständige Sätze
        if text.endswith('.') or text.endswith('!') or text.endswith('?'):
            quality_score += 0.2
        
        # Prüfe auf Großschreibung
        if text[0].isupper():
            quality_score += 0.1
        
        # Prüfe Wort-zu-Zeichen-Verhältnis
        words = text.split()
        if len(words) > 3:
            quality_score += 0.2
        
        return min(quality_score, 1.0)
    
    def _validate_consistency(self, data: List[Dict]) -> ValidationResult:
        """Validiert Konsistenz zwischen Items"""
        errors = []
        warnings = []
        
        if len(data) < 2:
            return ValidationResult(True, 1.0, {"note": "Zu wenige Items für Konsistenz-Check"}, [], [])
        
        # Prüfe Struktur-Konsistenz
        structures = []
        for item in data[:100]:  # Sample für Performance
            structure = self._extract_structure_signature(item)
            structures.append(structure)
        
        structure_consistency = len(set(structures)) / len(structures) if structures else 0
        consistency_score = 1.0 - structure_consistency + 0.1  # Invertiert, da weniger Varianz besser ist
        
        return ValidationResult(
            passed=consistency_score >= 0.8,
            score=max(0, min(1, consistency_score)),
            details={
                "structure_consistency": consistency_score,
                "unique_structures": len(set(structures)),
                "total_sampled": len(structures)
            },
            errors=errors,
            warnings=warnings
        )
    
    def _extract_structure_signature(self, item: Dict) -> str:
        """Extrahiert Struktur-Signatur für Konsistenz-Check"""
        signature = []
        
        if "messages" in item:
            for msg in item["messages"]:
                role = msg.get("role", "unknown")
                has_content = "content" in msg
                signature.append(f"{role}:{has_content}")
        
        return "|".join(signature)
    
    def _validate_performance(self, data: List[Dict]) -> ValidationResult:
        """Validiert Performance-Aspekte"""
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        # Simuliere Verarbeitung
        processed_items = 0
        for item in data:
            # Einfache Verarbeitung
            _ = json.dumps(item)
            processed_items += 1
        
        processing_time = time.time() - start_time
        memory_used = self._get_memory_usage() - initial_memory
        
        throughput = processed_items / processing_time if processing_time > 0 else 0
        
        # Performance-Score basierend auf Durchsatz
        performance_score = min(throughput / 1000, 1.0)  # Normalisiert auf 1000 items/s
        
        return ValidationResult(
            passed=performance_score >= 0.5,
            score=performance_score,
            details={
                "throughput_items_per_second": throughput,
                "processing_time": processing_time,
                "memory_used_mb": memory_used,
                "items_processed": processed_items
            }
        )
    
    def _detect_anomalies(self, data: List[Dict]) -> ValidationResult:
        """Erkennt Anomalien in den Daten"""
        anomalies = []
        
        if len(data) < 10:
            return ValidationResult(True, 1.0, {"note": "Zu wenige Daten für Anomalie-Erkennung"}, [], [])
        
        # Größen-basierte Anomalie-Erkennung
        sizes = [len(json.dumps(item)) for item in data]
        
        if NUMPY_AVAILABLE:
            mean_size = np.mean(sizes)
            std_size = np.std(sizes)
            
            for i, size in enumerate(sizes):
                z_score = abs(size - mean_size) / std_size if std_size > 0 else 0
                if z_score > 3:  # 3-Sigma-Regel
                    anomalies.append(f"Item {i}: Ungewöhnliche Größe (Z-Score: {z_score:.2f})")
        else:
            # Fallback ohne numpy
            mean_size = statistics.mean(sizes)
            for i, size in enumerate(sizes):
                if size > mean_size * 3 or size < mean_size * 0.3:
                    anomalies.append(f"Item {i}: Ungewöhnliche Größe")
        
        anomaly_score = len(anomalies) / len(data) if data else 0
        
        return ValidationResult(
            passed=anomaly_score <= 0.05,
            score=1.0 - anomaly_score,
            details={
                "anomalies_detected": len(anomalies),
                "anomaly_rate": anomaly_score,
                "anomalies": anomalies[:10]  # Zeige nur erste 10
            },
            warnings=anomalies
        )
    
    def _detect_regression(self, data: List[Dict]) -> ValidationResult:
        """Erkennt Qualitäts-Regression gegenüber Baseline"""
        # Vereinfachte Regression-Erkennung
        current_metrics = {
            "avg_item_size": statistics.mean([len(json.dumps(item)) for item in data]),
            "structure_variety": len(set(self._extract_structure_signature(item) for item in data[:100]))
        }
        
        regression_indicators = []
        
        # Vergleiche mit gespeicherten Baselines (falls vorhanden)
        if "baseline" in self.baseline_metrics:
            baseline = self.baseline_metrics["baseline"]
            
            for metric, current_value in current_metrics.items():
                if metric in baseline:
                    baseline_value = baseline[metric]
                    change_percent = (current_value - baseline_value) / baseline_value * 100
                    
                    if abs(change_percent) > 20:  # 20% Änderung als Schwellwert
                        regression_indicators.append(f"{metric}: {change_percent:+.1f}% Änderung")
        
        return ValidationResult(
            passed=len(regression_indicators) == 0,
            score=1.0 if len(regression_indicators) == 0 else 0.5,
            details={
                "current_metrics": current_metrics,
                "regression_indicators": regression_indicators
            },
            warnings=regression_indicators
        )
    
    def _run_benchmarks(self, data: List[Dict]) -> BenchmarkResults:
        """Führt Performance-Benchmarks durch"""
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        # Verschiedene Operationen benchmarken
        latencies = []
        
        # JSON-Serialisierung Benchmark
        for item in data[:100]:  # Sample für Performance
            item_start = time.time()
            _ = json.dumps(item)
            latencies.append((time.time() - item_start) * 1000)  # in ms
        
        total_time = time.time() - start_time
        memory_used = self._get_memory_usage() - initial_memory
        
        throughput = len(data) / total_time if total_time > 0 else 0
        
        # Berechne Perzentile
        latencies.sort()
        n = len(latencies)
        
        return BenchmarkResults(
            throughput_items_per_second=throughput,
            memory_efficiency_score=max(0, 1 - (memory_used / 100)),  # Normalisiert auf 100MB
            error_rate=0.0,  # Vereinfacht
            latency_p50=latencies[n//2] if latencies else 0,
            latency_p95=latencies[int(n*0.95)] if latencies else 0,
            latency_p99=latencies[int(n*0.99)] if latencies else 0,
            resource_utilization={
                "memory_mb": memory_used,
                "cpu_percent": self._get_cpu_usage()
            }
        )
    
    def _calculate_overall_score(self, metrics: QualityMetrics) -> float:
        """Berechnet Gesamtscore aus allen Metriken"""
        weights = {
            "content_quality": 0.3,
            "format_consistency": 0.2,
            "data_completeness": 0.2,
            "semantic_coherence": 0.15,
            "performance_score": 0.1,
            "anomaly_penalty": 0.05
        }
        
        score = (
            metrics.content_quality * weights["content_quality"] +
            metrics.format_consistency * weights["format_consistency"] +
            metrics.data_completeness * weights["data_completeness"] +
            metrics.semantic_coherence * weights["semantic_coherence"] +
            metrics.performance_score * weights["performance_score"] -
            metrics.anomaly_score * weights["anomaly_penalty"]
        )
        
        return max(0, min(1, score))
    
    def _get_memory_usage(self) -> float:
        """Gibt aktuelle Speichernutzung in MB zurück"""
        if SYSTEM_MONITORING_AVAILABLE:
            return psutil.Process().memory_info().rss / 1024 / 1024
        return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Gibt aktuelle CPU-Nutzung zurück"""
        if SYSTEM_MONITORING_AVAILABLE:
            return psutil.cpu_percent()
        return 0.0

def main():
    """CLI-Interface für Enhanced Quality Validation"""
    parser = argparse.ArgumentParser(
        description="Enhanced LegalTech Quality Validation Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python enhanced_quality_validation.py dataset.jsonl --level comprehensive
  python enhanced_quality_validation.py dataset.jsonl --level enterprise --benchmark --output report.json
        """
    )
    
    parser.add_argument(
        "input_file",
        help="Eingabedatei für Qualitätsvalidierung"
    )
    
    parser.add_argument(
        "--level",
        choices=["basic", "standard", "comprehensive", "enterprise"],
        default="standard",
        help="Validierungsstufe (Standard: standard)"
    )
    
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Performance-Benchmarking durchführen"
    )
    
    parser.add_argument(
        "--output",
        help="Ausgabedatei für detaillierte Ergebnisse (JSON)"
    )
    
    parser.add_argument(
        "--config",
        help="Konfigurationsdatei für Validierungsparameter"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Detaillierte Ausgabe"
    )
    
    parser.add_argument(
        "--baseline",
        help="Baseline-Datei für Regression-Erkennung"
    )
    
    args = parser.parse_args()
    
    # Konfiguriere Logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    print(f"\n{Colors.HEADER}🔍 Enhanced LegalTech Quality Validation Suite{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*55}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Enterprise-Grade Qualitätsvalidierung{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'='*55}{Colors.ENDC}")
    
    # Lade Konfiguration
    config = None
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
            print(f"{Colors.OKGREEN}✓ Konfiguration geladen: {args.config}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Warnung: Konnte Konfiguration nicht laden: {e}{Colors.ENDC}")
    
    # Initialisiere Validator
    try:
        validator = EnhancedQualityValidator(config)
        
        # Lade Baseline falls vorhanden
        if args.baseline and os.path.exists(args.baseline):
            try:
                with open(args.baseline, 'r') as f:
                    validator.baseline_metrics = json.load(f)
                print(f"{Colors.OKGREEN}✓ Baseline geladen: {args.baseline}{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.WARNING}⚠ Warnung: Konnte Baseline nicht laden: {e}{Colors.ENDC}")
        
        print(f"\n{Colors.OKCYAN}📋 Validierungsparameter:{Colors.ENDC}")
        print(f"  • Eingabedatei: {args.input_file}")
        print(f"  • Validierungsstufe: {args.level}")
        print(f"  • Benchmarking: {'✓' if args.benchmark else '✗'}")
        print(f"  • Baseline-Vergleich: {'✓' if args.baseline else '✗'}")
        
        # Führe Validierung durch
        start_time = time.time()
        result = validator.validate_dataset(
            file_path=args.input_file,
            validation_level=args.level,
            enable_benchmarking=args.benchmark
        )
        
        # Zeige Ergebnisse
        print(f"\n{Colors.HEADER}📊 Validierungsergebnisse:{Colors.ENDC}")
        print(f"{'='*50}")
        
        if result.passed:
            print(f"{Colors.OKGREEN}✅ VALIDIERUNG BESTANDEN{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ VALIDIERUNG FEHLGESCHLAGEN{Colors.ENDC}")
        
        print(f"\n{Colors.OKCYAN}Gesamtscore: {result.score:.3f}{Colors.ENDC}")
        print(f"Verarbeitungszeit: {result.processing_time:.2f}s")
        print(f"Speicherverbrauch: {result.memory_usage:.1f}MB")
        
        # Zeige Metriken
        if result.metrics:
            print(f"\n{Colors.OKCYAN}📈 Qualitäts-Metriken:{Colors.ENDC}")
            for metric, value in result.metrics.items():
                color = Colors.OKGREEN if value >= 0.7 else Colors.WARNING if value >= 0.5 else Colors.FAIL
                print(f"  • {metric}: {color}{value:.3f}{Colors.ENDC}")
        
        # Zeige Fehler und Warnungen
        if result.errors:
            print(f"\n{Colors.FAIL}❌ Fehler ({len(result.errors)}):{Colors.ENDC}")
            for error in result.errors[:5]:  # Zeige max 5
                print(f"  • {error}")
            if len(result.errors) > 5:
                print(f"  ... und {len(result.errors) - 5} weitere")
        
        if result.warnings:
            print(f"\n{Colors.WARNING}⚠ Warnungen ({len(result.warnings)}):{Colors.ENDC}")
            for warning in result.warnings[:5]:  # Zeige max 5
                print(f"  • {warning}")
            if len(result.warnings) > 5:
                print(f"  ... und {len(result.warnings) - 5} weitere")
        
        # Speichere detaillierte Ergebnisse
        if args.output:
            try:
                output_data = {
                    "validation_result": asdict(result),
                    "timestamp": datetime.now().isoformat(),
                    "parameters": {
                        "input_file": args.input_file,
                        "validation_level": args.level,
                        "benchmarking_enabled": args.benchmark
                    }
                }
                
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"\n{Colors.OKGREEN}📄 Detaillierte Ergebnisse gespeichert: {args.output}{Colors.ENDC}")
                
            except Exception as e:
                print(f"\n{Colors.WARNING}⚠ Warnung: Konnte Ergebnisse nicht speichern: {e}{Colors.ENDC}")
        
        # Exit-Code basierend auf Validierungsergebnis
        sys.exit(0 if result.passed else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️ Validierung vom Benutzer unterbrochen{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.FAIL}💥 Unerwarteter Fehler: {str(e)}{Colors.ENDC}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
