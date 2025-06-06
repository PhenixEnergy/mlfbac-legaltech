# 🏗️ LegalTech NLP Pipeline - Folder Structure Redesign Plan

**Date:** June 5, 2025  
**Objective:** Create a logical, scalable, and maintainable folder structure  
**Status:** 🚀 READY FOR IMPLEMENTATION

---

## 🎯 Current Structure Issues

### ❌ **Problems Identified:**
1. **Root Clutter**: Too many report files in root directory
2. **Script Organization**: All scripts mixed together regardless of function
3. **Documentation Spread**: Documentation files scattered across locations
4. **Unclear Hierarchy**: No clear separation between development and production assets
5. **Inconsistent Naming**: Mixed conventions for files and folders

---

## 🏗️ Proposed New Structure

```
LegalTech-NLP-Pipeline/
│
├── 📚 docs/                                    # All Documentation
│   ├── index.html                             # Main documentation entry
│   ├── consolidated_documentation.html        # Complete reference
│   └── assets/                                # Documentation assets (images, css)
│
├── 🔧 src/                                     # Source Code
│   ├── core/                                  # Core processing modules
│   │   ├── segmentation.py                    # Text segmentation logic
│   │   ├── prompt_generation.py               # Prompt creation
│   │   └── data_preparation.py                # Data prep utilities
│   ├── pipeline/                              # Pipeline orchestration
│   │   ├── orchestrator.py                    # Main pipeline coordinator
│   │   ├── integration.py                     # System integration
│   │   └── quality_validation.py              # Quality assurance
│   ├── utils/                                 # Utility modules
│   │   ├── converters.py                      # Format conversion tools
│   │   └── config_manager.py                  # Configuration handling
│   └── config/                                # Configuration files
│       └── optimization_config.json           # Main configuration
│
├── 💾 data/                                   # All Data Assets
│   ├── raw/                                   # Original unprocessed data
│   │   └── gutachten_alle_seiten_neu.json
│   ├── processed/                             # Processed datasets
│   │   ├── fine_tuning/                       # Fine-tuning ready data
│   │   │   ├── small/                         # Development datasets
│   │   │   ├── medium/                        # Testing datasets  
│   │   │   └── production/                    # Production datasets
│   │   └── rag_training/                      # RAG system data
│   │       ├── knowledge_bases/               # Knowledge base files
│   │       └── training_sets/                 # Training datasets
│   └── temp/                                  # Temporary processing files
│
├── 🧪 tests/                                  # Testing suite
│   ├── unit/                                  # Unit tests
│   ├── integration/                           # Integration tests
│   └── performance/                           # Performance benchmarks
│
├── 📊 reports/                                # Project reports & analysis
│   ├── development/                           # Development reports
│   ├── performance/                           # Performance analysis
│   └── project_management/                    # PM documentation
│
├── 🗄️ archive/                                # Historical preservation
│   ├── legacy_code/                           # Old script versions
│   ├── legacy_docs/                           # Old documentation
│   └── process_reports/                       # Development process docs
│
├── 🔧 tools/                                  # Development tools
│   ├── open_documentation.bat                 # Quick access scripts
│   └── setup_scripts/                         # Environment setup
│
├── 📋 README.md                               # Project overview
├── 📝 PROJECT_STRUCTURE.md                    # This structure documentation
├── ⚙️ requirements.txt                        # Python dependencies
└── 🚀 setup.py                               # Package setup configuration
```

---

## 🎯 Design Principles

### ✅ **Benefits of New Structure:**

1. **🎯 Purpose-Driven Organization**
   - Clear separation between source code, data, documentation, and tools
   - Logical grouping by functionality rather than file type

2. **📈 Scalability**
   - Easy to add new modules without cluttering existing directories
   - Support for different data sizes (small/medium/production)

3. **👥 Team Collaboration**
   - Clear ownership boundaries for different team roles
   - Intuitive navigation for new team members

4. **🔧 Development Workflow**
   - Separate testing environment from production code
   - Configuration management centralized

5. **📚 Documentation Strategy**
   - Single docs/ folder for all documentation needs
   - Clear separation from code for documentation teams

---

## 🚀 Migration Strategy

### Phase 1: Create New Folder Structure
```cmd
mkdir src\core src\pipeline src\utils src\config
mkdir data\raw data\processed\fine_tuning\small data\processed\fine_tuning\medium data\processed\fine_tuning\production
mkdir data\processed\rag_training\knowledge_bases data\processed\rag_training\training_sets data\temp
mkdir tests\unit tests\integration tests\performance
mkdir reports\development reports\performance reports\project_management
mkdir archive\legacy_code archive\legacy_docs archive\process_reports
mkdir tools\setup_scripts
mkdir docs\assets
```

### Phase 2: Migrate Source Code
```cmd
# Core processing modules
move Scripts\enhanced_segmentation.py src\core\segmentation.py
move Scripts\optimized_prompt_generation.py src\core\prompt_generation.py
move Scripts\segment_and_prepare_training_data.py src\core\data_preparation.py
move Scripts\prepare_rag_training_data.py src\core\rag_data_preparation.py

# Pipeline modules
move Scripts\advanced_pipeline_orchestrator.py src\pipeline\orchestrator.py
move Scripts\optimization_integration.py src\pipeline\integration.py
move Scripts\enhanced_quality_validation.py src\pipeline\quality_validation.py

# Utilities
move Scripts\jsonl_converter.py src\utils\converters.py

# Configuration
move Scripts\optimization_config.json src\config\optimization_config.json
```

### Phase 3: Migrate Data Assets
```cmd
# Raw data
move Database\Original_Data\gutachten_alle_seiten_neu.json data\raw\

# Fine-tuning data
move Database\Fine_Tuning\gutachten_alle_seiten_neu_max_segmented_prepared.jsonl data\processed\fine_tuning\production\
move Database\Fine_Tuning\gutachten_alle_seiten_neu_2_Mio_segmented_prepared.jsonl data\processed\fine_tuning\medium\
move Database\Fine_Tuning\gutachten_alle_seiten_neu_1_5_Mio_segmented_prepared.jsonl data\processed\fine_tuning\medium\

# RAG training data
move Database\RAG_Training\*knowledge_base* data\processed\rag_training\knowledge_bases\
move Database\RAG_Training\*training* data\processed\rag_training\training_sets\
```

### Phase 4: Migrate Documentation
```cmd
# Main documentation
move Documentation\consolidated_documentation.html docs\
move Documentation\index.html docs\

# Archive legacy documentation
move Archive\Documentation\* archive\legacy_docs\
```

### Phase 5: Organize Reports
```cmd
# Development reports
move Archive\DOCUMENTATION_COMPLETION_REPORT.md reports\development\
move Archive\ENHANCEMENT_COMPLETION_REPORT_v3.md reports\development\

# Project management
move DOCUMENTATION_CONSOLIDATION_SUMMARY.md reports\project_management\
move WORKSPACE_CLEANUP_PLAN.md reports\project_management\
move WORKSPACE_CLEANUP_REPORT.md reports\project_management\
move FINAL_PROJECT_COMPLETION_REPORT.md reports\project_management\
move PROJECT_FILE_INVENTORY.md reports\project_management\
```

### Phase 6: Tools and Utilities
```cmd
move open_documentation.bat tools\
```

### Phase 7: Archive Legacy
```cmd
# Archive old script versions
move Archive\prepare_rag_training_data_v2.py archive\legacy_code\

# Archive any remaining legacy items
move Scripts\semantic_segmentation.py archive\legacy_code\
```

---

## 📋 Implementation Checklist

### ✅ **Pre-Migration:**
- [ ] Backup current workspace
- [ ] Verify all files are committed to git
- [ ] Document current dependencies

### ✅ **Migration:**
- [ ] Create new folder structure
- [ ] Move source code files with logical renaming
- [ ] Reorganize data assets by type and size
- [ ] Consolidate documentation
- [ ] Organize reports by category
- [ ] Update file references and imports

### ✅ **Post-Migration:**
- [ ] Update all file paths in scripts
- [ ] Update documentation references
- [ ] Test all functionality
- [ ] Update open_documentation.bat path
- [ ] Create new PROJECT_STRUCTURE.md

---

## 🔧 File Mapping Guide

### **Source Code Mapping:**
| Old Location | New Location | Reason |
|-------------|-------------|---------|
| `Scripts/enhanced_segmentation.py` | `src/core/segmentation.py` | Core functionality |
| `Scripts/optimized_prompt_generation.py` | `src/core/prompt_generation.py` | Core functionality |
| `Scripts/advanced_pipeline_orchestrator.py` | `src/pipeline/orchestrator.py` | Pipeline management |
| `Scripts/jsonl_converter.py` | `src/utils/converters.py` | Utility function |

### **Data Mapping:**
| Old Location | New Location | Reason |
|-------------|-------------|---------|
| `Database/Original_Data/` | `data/raw/` | Clearer naming |
| `Database/Fine_Tuning/` | `data/processed/fine_tuning/` | Purpose-based organization |
| `Database/RAG_Training/` | `data/processed/rag_training/` | Type-based separation |

### **Documentation Mapping:**
| Old Location | New Location | Reason |
|-------------|-------------|---------|
| `Documentation/` | `docs/` | Standard naming convention |
| Various `*.md` reports | `reports/project_management/` | Centralized reporting |

---

## 🎉 Expected Outcomes

### ✅ **Improved Organization:**
- **90% reduction** in root directory clutter
- **Clear separation** of concerns
- **Intuitive navigation** for team members

### ✅ **Enhanced Maintainability:**
- **Modular structure** supports independent development
- **Clear dependency relationships**
- **Easier testing and deployment**

### ✅ **Better Scalability:**
- **Room for growth** in each category
- **Standard conventions** for new additions
- **Version control friendly** structure

---

**🚀 Ready for Implementation:** Structure verified and migration path planned!
