#!/bin/bash
# Helper script to create OpenShift secret for BFSI Document Intelligence

set -e

NAMESPACE="dsdemo1"
SECRET_NAME="bfsi-doc-intelligence-secrets"

echo "=== Creating Secret for BFSI Document Intelligence ==="
echo ""
echo "Which LLM provider do you want to use?"
echo "1. OpenAI"
echo "2. Anthropic (Claude)"
echo "3. Custom LiteLLM Endpoint"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        read -p "Enter OPENAI_API_KEY: " openai_key
        read -p "Enter OPENAI_MODEL (default: gpt-4-turbo-preview): " openai_model
        openai_model=${openai_model:-gpt-4-turbo-preview}
        read -p "Enter TAVILY_API_KEY: " tavily_key
        
        oc create secret generic $SECRET_NAME \
            --from-literal=OPENAI_API_KEY="$openai_key" \
            --from-literal=OPENAI_MODEL="$openai_model" \
            --from-literal=TAVILY_API_KEY="$tavily_key" \
            -n $NAMESPACE --dry-run=client -o yaml | oc apply -f -
        ;;
    2)
        read -p "Enter ANTHROPIC_API_KEY: " anthropic_key
        read -p "Enter ANTHROPIC_MODEL (default: claude-3-opus-20240229): " anthropic_model
        anthropic_model=${anthropic_model:-claude-3-opus-20240229}
        read -p "Enter TAVILY_API_KEY: " tavily_key
        
        oc create secret generic $SECRET_NAME \
            --from-literal=ANTHROPIC_API_KEY="$anthropic_key" \
            --from-literal=ANTHROPIC_MODEL="$anthropic_model" \
            --from-literal=TAVILY_API_KEY="$tavily_key" \
            -n $NAMESPACE --dry-run=client -o yaml | oc apply -f -
        ;;
    3)
        read -p "Enter CUSTOM_LLM_ENDPOINT: " custom_endpoint
        read -p "Enter CUSTOM_LLM_MODEL: " custom_model
        read -p "Enter CUSTOM_LLM_API_KEY (optional, press Enter to skip): " custom_key
        read -p "Enter TAVILY_API_KEY: " tavily_key
        
        if [ -z "$custom_key" ]; then
            oc create secret generic $SECRET_NAME \
                --from-literal=CUSTOM_LLM_ENDPOINT="$custom_endpoint" \
                --from-literal=CUSTOM_LLM_MODEL="$custom_model" \
                --from-literal=TAVILY_API_KEY="$tavily_key" \
                -n $NAMESPACE --dry-run=client -o yaml | oc apply -f -
        else
            oc create secret generic $SECRET_NAME \
                --from-literal=CUSTOM_LLM_ENDPOINT="$custom_endpoint" \
                --from-literal=CUSTOM_LLM_MODEL="$custom_model" \
                --from-literal=CUSTOM_LLM_API_KEY="$custom_key" \
                --from-literal=TAVILY_API_KEY="$tavily_key" \
                -n $NAMESPACE --dry-run=client -o yaml | oc apply -f -
        fi
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Secret created successfully!"
echo ""
echo "Updating deployment..."
oc apply -f deployment.yaml -n $NAMESPACE
echo ""
echo "Restarting pods to pick up new environment variables..."
oc rollout restart deployment bfsi-doc-intelligence -n $NAMESPACE
echo ""
echo "✅ Done! Check pod status with: oc get pods -l app=bfsi-doc-intelligence -n $NAMESPACE"

