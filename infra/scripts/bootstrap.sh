#!/bin/bash
set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────────

PROJECT_ID="${1:-}"
if [ -z "$PROJECT_ID" ]; then
  echo "Usage: ./bootstrap.sh <your-gcp-project-id>"
  exit 1
fi

SA_NAME="terraform"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="$HOME/.config/quarterwatch/terraform-key.json"

# ── Login ──────────────────────────────────────────────────────────────────

echo ">>> Logging into GCP..."
gcloud auth login
gcloud config set project "$PROJECT_ID"

# ── Enable IAM API ─────────────────────────────────────────────────────────

echo ">>> Enabling IAM API..."
gcloud services enable iam.googleapis.com

# ── Create Terraform service account ───────────────────────────────────────

echo ">>> Creating Terraform service account..."
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="Terraform" \
  --project="$PROJECT_ID" || echo "Service account already exists, continuing."

# ── Grant permissions ──────────────────────────────────────────────────────

echo ">>> Granting permissions..."

ROLES=(
  "roles/editor"
  "roles/iam.securityAdmin"
  "roles/secretmanager.admin"
  "roles/cloudsql.admin"
  "roles/run.admin"
  "roles/cloudtasks.admin"
  "roles/cloudscheduler.admin"
  "roles/artifactregistry.admin"
  "roles/storage.admin"
)

for ROLE in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" \
    --quiet
  echo "  Granted $ROLE"
done

# ── Generate key file ──────────────────────────────────────────────────────

echo ">>> Generating key file..."
mkdir -p "$(dirname "$KEY_FILE")"
gcloud iam service-accounts keys create "$KEY_FILE" \
  --iam-account="$SA_EMAIL"

# ── Done ───────────────────────────────────────────────────────────────────

echo ""
echo "Bootstrap complete."
echo ""
echo "Key saved to: $KEY_FILE"
echo ""
echo "Run this before terraform apply:"
echo "  export GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE"
echo ""
echo "Then from the infra/ directory:"
echo "  terraform init"
echo "  terraform plan"
echo "  terraform apply"