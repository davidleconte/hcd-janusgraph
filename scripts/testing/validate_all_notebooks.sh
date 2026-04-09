#!/bin/bash
# Validate all 18 banking notebooks
# Usage: bash scripts/testing/validate_all_notebooks.sh

set -e

NOTEBOOK_DIR="banking/notebooks"
OUTPUT_DIR="/tmp/notebook_validation"
LOG_FILE="/tmp/notebook_validation.log"
RESULTS_FILE="/tmp/notebook_results.txt"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Clear previous results
> "$LOG_FILE"
> "$RESULTS_FILE"

echo "========================================" | tee -a "$LOG_FILE"
echo "Banking Notebook Validation" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# List of notebooks to validate
NOTEBOOKS=(
    "01_Sanctions_Screening_Demo.ipynb"
    "02_AML_Structuring_Detection_Demo.ipynb"
    "03_Fraud_Detection_Demo.ipynb"
    "04_Customer_360_View_Demo.ipynb"
    "05_Advanced_Analytics_OLAP.ipynb"
    "06_TBML_Detection_Demo.ipynb"
    "07_Insider_Trading_Detection_Demo.ipynb"
    "08_UBO_Discovery_Demo.ipynb"
    "09_Community_Detection_Demo.ipynb"
    "10_Integrated_Architecture_Demo.ipynb"
    "11_Streaming_Pipeline_Demo.ipynb"
    "12_API_Integration_Demo.ipynb"
    "13_Time_Travel_Queries_Demo.ipynb"
    "14_Entity_Resolution_Demo.ipynb"
    "15_Graph_Embeddings_ML_Demo.ipynb"
    "16_APP_Fraud_Mule_Chains.ipynb"
    "17_Account_Takeover_ATO_Demo.ipynb"
    "18_Corporate_Vendor_Fraud_Demo.ipynb"
)

PASSED=0
FAILED=0
TOTAL=${#NOTEBOOKS[@]}

# Execute each notebook
for notebook in "${NOTEBOOKS[@]}"; do
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    echo "Executing: $notebook" | tee -a "$LOG_FILE"
    echo "Started: $(date +%H:%M:%S)" | tee -a "$LOG_FILE"
    
    START_TIME=$(date +%s)
    
    # Execute notebook
    if conda run -n janusgraph-analysis python -m nbconvert \
        --to notebook \
        --execute \
        --ExecutePreprocessor.timeout=300 \
        "$NOTEBOOK_DIR/$notebook" \
        --output "$OUTPUT_DIR/${notebook%.ipynb}_executed.ipynb" \
        >> "$LOG_FILE" 2>&1; then
        
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        echo "✅ PASSED ($DURATION seconds)" | tee -a "$LOG_FILE"
        echo "✅ $notebook - PASSED ($DURATION seconds)" >> "$RESULTS_FILE"
        ((PASSED++))
    else
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        echo "❌ FAILED ($DURATION seconds)" | tee -a "$LOG_FILE"
        echo "❌ $notebook - FAILED ($DURATION seconds)" >> "$RESULTS_FILE"
        ((FAILED++))
    fi
    
    echo "" | tee -a "$LOG_FILE"
done

# Summary
echo "========================================" | tee -a "$LOG_FILE"
echo "Validation Summary" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Total Notebooks: $TOTAL" | tee -a "$LOG_FILE"
echo "Passed: $PASSED" | tee -a "$LOG_FILE"
echo "Failed: $FAILED" | tee -a "$LOG_FILE"
echo "Success Rate: $(awk "BEGIN {printf \"%.1f\", ($PASSED/$TOTAL)*100}")%" | tee -a "$LOG_FILE"
echo "Completed: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Display results
echo ""
echo "Results saved to: $RESULTS_FILE"
echo "Full log saved to: $LOG_FILE"
echo ""
cat "$RESULTS_FILE"

# Exit with error if any notebooks failed
if [ $FAILED -gt 0 ]; then
    exit 1
fi

exit 0

# Made with Bob
