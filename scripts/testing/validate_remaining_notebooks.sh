#!/bin/bash
# Validate remaining 17 banking notebooks (02-18)
# Usage: bash scripts/testing/validate_remaining_notebooks.sh

NOTEBOOK_DIR="banking/notebooks"
OUTPUT_DIR="/tmp/notebook_validation"
RESULTS_FILE="/tmp/notebook_results_remaining.txt"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Clear previous results
> "$RESULTS_FILE"

echo "Validating remaining 17 notebooks..."
echo ""

# List of remaining notebooks (02-18)
NOTEBOOKS=(
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

# Execute each notebook
for notebook in "${NOTEBOOKS[@]}"; do
    echo "Executing: $notebook"
    START_TIME=$(date +%s)
    
    # Execute notebook (don't exit on error)
    if conda run -n janusgraph-analysis python -m nbconvert \
        --to notebook \
        --execute \
        --ExecutePreprocessor.timeout=300 \
        "$NOTEBOOK_DIR/$notebook" \
        --output "$OUTPUT_DIR/${notebook%.ipynb}_executed.ipynb" \
        > /dev/null 2>&1; then
        
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        echo "✅ PASSED ($DURATION seconds)"
        echo "✅ $notebook - PASSED ($DURATION seconds)" >> "$RESULTS_FILE"
        ((PASSED++))
    else
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        echo "❌ FAILED ($DURATION seconds)"
        echo "❌ $notebook - FAILED ($DURATION seconds)" >> "$RESULTS_FILE"
        ((FAILED++))
    fi
    echo ""
done

# Summary
echo "========================================"
echo "Summary:"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "========================================"
echo ""
cat "$RESULTS_FILE"

exit 0

# Made with Bob
