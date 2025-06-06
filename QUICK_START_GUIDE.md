# 🚀 LegalTech Pipeline - Quick Start Guide

## **Installation & Setup**
```bash
# Navigate to project directory
cd "d:\School\Studium\Semester 6\MLFB-AC\LegalTech\Git\mlfbac-legaltech"

# Check pipeline status
python main.py status
```

## **Basic Usage Examples**

### **1. Convert Documents**
```bash
# JSON to JSONL
python main.py convert --input data.json --output data.jsonl

# JSONL to JSON
python main.py convert --input data.jsonl --output data.json
```

### **2. Segment Text**
```bash
# Enhanced segmentation (demo)
python main.py segment --input data.jsonl --strategy enhanced

# Training segmentation (real processing)
python main.py segment --input data.jsonl --strategy training
```

### **3. Prepare RAG Data**
```bash
# Generate RAG training data
python main.py rag-prepare --input segmented_data.jsonl --output rag_data
```

### **4. Validate Quality**
```bash
# Run quality validation
python main.py validate --input your_data.jsonl
```

### **5. Generate Prompts**
```bash
# Optimized prompt generation
python main.py prompt-gen --input data.jsonl --output prompts.jsonl
```

## **Complete Workflow Example**
```bash
# Step 1: Convert raw data
python main.py convert --input "data\Original_Data\gutachten_alle_seiten_neu.json" --output "converted.jsonl"

# Step 2: Segment for training
python main.py segment --input "converted.jsonl" --strategy training

# Step 3: Prepare for RAG
python main.py rag-prepare --input "training_segments.jsonl"

# Step 4: Validate quality
python main.py validate --input "rag_output.jsonl"
```

## **Get Help**
```bash
# General help
python main.py --help

# Command-specific help
python main.py convert --help
python main.py segment --help
python main.py rag-prepare --help
python main.py validate --help
```

## **Available Strategies**
- **Segment strategies:** `enhanced`, `semantic`, `training`
- **Optimization modes:** `segmentation`, `rag`, `fine_tuning`
- **Output modes:** `fine_tuning`, `rag_training`, `rag_knowledge_base`, `analysis_report`

## **Logging**
- **Log levels:** `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Example:** `python main.py --log-level DEBUG convert --input data.json --output data.jsonl`

---
**✅ All commands verified and working!** 🎯
