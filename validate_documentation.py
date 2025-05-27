#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation Validation Script
Verifies completeness and accessibility of all documentation files
"""

import os
from pathlib import Path

def validate_documentation_structure():
    """Validates the documentation structure"""
    print("📋 LegalTech NLP Pipeline - Documentation Validation")
    print("=" * 65)
    
    # Core documentation files
    core_docs = [
        "README.md",
        "DOCUMENTATION_INDEX.md", 
        "DEVELOPER_GUIDE.md",
        "API_REFERENCE.md",
        "CONFIGURATION.md",
        "TROUBLESHOOTING.md",
        "PERFORMANCE_BENCHMARKS.md",
        "DOCUMENTATION_COMPLETION_REPORT.md"
    ]
    
    # Example files
    example_files = [
        "Examples/README.md",
        "Examples/basic_usage.py",
        "Examples/advanced_configuration.py",
        "Examples/custom_integrations.py",
        "Examples/performance_optimization.py",
        "Examples/quality_validation.py",
        "Examples/troubleshooting_helpers.py"
    ]
    
    # Interactive documentation
    interactive_docs = [
        "Documentation/index.html"
    ]
    
    # Project structure files
    structure_files = [
        "PROJECT_STRUCTURE.md",
        "PROJECT_FILE_INVENTORY.md"
    ]
    
    all_files = {
        "Core Documentation": core_docs,
        "Example Files": example_files,
        "Interactive Documentation": interactive_docs,
        "Project Structure": structure_files
    }
    
    total_files = 0
    found_files = 0
    
    for category, files in all_files.items():
        print(f"\n📁 {category}:")
        
        for file_path in files:
            total_files += 1
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"  ✅ {file_path} ({file_size:,} bytes)")
                found_files += 1
            else:
                print(f"  ❌ {file_path} (Missing)")
    
    # Summary
    print("\n" + "=" * 65)
    print(f"📊 Documentation Summary:")
    print(f"  📁 Total files expected: {total_files}")
    print(f"  ✅ Files found: {found_files}")
    print(f"  ❌ Files missing: {total_files - found_files}")
    print(f"  📈 Completeness: {(found_files/total_files)*100:.1f}%")
    
    if found_files == total_files:
        print("\n🎉 Documentation is COMPLETE!")
        return True
    else:
        print(f"\n⚠️ Documentation is {found_files}/{total_files} complete")
        return False

def check_file_sizes():
    """Checks if files have reasonable content"""
    print("\n🔍 Content Validation:")
    
    important_files = {
        "README.md": 5000,  # Should be substantial
        "PERFORMANCE_BENCHMARKS.md": 10000,  # Should be detailed
        "Examples/advanced_configuration.py": 15000,  # Should be comprehensive
        "Examples/custom_integrations.py": 20000,  # Should be extensive
        "Examples/troubleshooting_helpers.py": 15000,  # Should be detailed
    }
    
    for file_path, min_size in important_files.items():
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if size >= min_size:
                print(f"  ✅ {file_path}: {size:,} bytes (Good)")
            else:
                print(f"  ⚠️ {file_path}: {size:,} bytes (Below {min_size:,})")
        else:
            print(f"  ❌ {file_path}: Missing")

def generate_final_report():
    """Generates final validation report"""
    print("\n📄 Final Validation Report:")
    print("-" * 40)
    
    # Check key achievements
    achievements = [
        ("Advanced Configuration Examples", "Examples/advanced_configuration.py"),
        ("Custom Integration Framework", "Examples/custom_integrations.py"), 
        ("Troubleshooting Utilities", "Examples/troubleshooting_helpers.py"),
        ("Performance Benchmarks", "PERFORMANCE_BENCHMARKS.md"),
        ("Completion Report", "DOCUMENTATION_COMPLETION_REPORT.md"),
        ("Updated Examples README", "Examples/README.md"),
        ("Updated Documentation Index", "DOCUMENTATION_INDEX.md")
    ]
    
    completed = 0
    total = len(achievements)
    
    for achievement, file_path in achievements:
        if os.path.exists(file_path):
            print(f"  ✅ {achievement}")
            completed += 1
        else:
            print(f"  ❌ {achievement}")
    
    print(f"\n📊 Overall Progress: {completed}/{total} ({(completed/total)*100:.0f}%)")
    
    if completed == total:
        print("🎉 ALL DOCUMENTATION TASKS COMPLETED!")
        print("The LegalTech NLP Pipeline is now fully documented and production-ready.")
    else:
        print(f"⚠️ {total - completed} tasks remaining")

def main():
    """Main validation function"""
    structure_complete = validate_documentation_structure()
    check_file_sizes()
    generate_final_report()
    
    print("\n" + "=" * 65)
    if structure_complete:
        print("✅ Documentation validation PASSED")
        print("🚀 Ready for production use!")
    else:
        print("❌ Documentation validation FAILED")
        print("📝 Please address missing files")

if __name__ == "__main__":
    main()
