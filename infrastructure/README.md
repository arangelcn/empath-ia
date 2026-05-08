# Infraestrutura empatIA — GKE Autopilot + Terraform

## Pré-requisitos

- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.6
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud`)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- Projeto GCP com billing habilitado

---

## 1. Configuração inicial (apenas uma vez)

### 1.1 Criar bucket para o state do Terraform

```bash
export PROJECT_ID="empathia-462921"
export REGION="us-central1"

gsutil mb -l $REGION gs://${PROJECT_ID}-terraform-state
gsutil versioning set on gs://${PROJECT_ID}-terraform-state
```

### 1.2 Autenticar no GCP

```bash
gcloud auth application-default login
gcloud config set project $PROJECT_ID
```

### 1.3 Configurar variáveis do Terraform

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars com seus valores reais
```

### 1.4 Inicializar e aplicar Terraform

```bash
terraform init \
  -backend-config="bucket=${PROJECT_ID}-terraform-state" \
  -backend-config="prefix=terraform/state"

terraform plan
terraform apply
```

O `terraform apply` irá:
- Habilitar as APIs GCP necessárias
- Criar a VPC + Cloud NAT
- Criar o cluster GKE Autopilot
- Criar o Artifact Registry
- Criar os secrets no Secret Manager
- Criar a Service Account com Workload Identity

---

## 2. Conectar ao cluster

```bash
# O comando exato é mostrado no output do terraform
gcloud container clusters get-credentials empatia-cluster \
  --region us-central1 \
  --project empathia-462921
```

---

## 3. Primeiro deploy manual

Após o `terraform apply`, faça o primeiro deploy:

```bash
export PROJECT_ID="empathia-462921"
export REGION="us-central1"
export REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/empatia-images"
export TAG="v1.0.0"

# Autenticar Docker
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build e push de todas as imagens
for svc in gateway-service ai-service avatar-service emotion-service voice-service; do
  docker build -t ${REGISTRY}/${svc}:${TAG} services/${svc}/
  docker push ${REGISTRY}/${svc}:${TAG}
done

docker build -t ${REGISTRY}/web-ui:${TAG} apps/web-ui/
docker build -t ${REGISTRY}/admin-panel:${TAG} apps/admin-panel/
docker push ${REGISTRY}/web-ui:${TAG}
docker push ${REGISTRY}/admin-panel:${TAG}

# Criar secret no Kubernetes (lê do Secret Manager)
kubectl apply -f infrastructure/k8s/namespace.yaml
kubectl create secret generic empatia-secrets \
  --namespace empatia \
  --from-literal=OPENAI_API_KEY="$(gcloud secrets versions access latest --secret=empatia-openai-api-key)" \
  --from-literal=DID_API_USERNAME="$(gcloud secrets versions access latest --secret=empatia-did-api-username)" \
  --from-literal=DID_API_PASSWORD="$(gcloud secrets versions access latest --secret=empatia-did-api-password)" \
  --from-literal=MONGO_ROOT_PASSWORD="$(gcloud secrets versions access latest --secret=empatia-mongo-root-password)" \
  --from-literal=REDIS_PASSWORD="$(gcloud secrets versions access latest --secret=empatia-redis-password)" \
  --from-literal=JWT_SECRET_KEY="$(gcloud secrets versions access latest --secret=empatia-jwt-secret-key)"

# Substituir placeholders e aplicar manifests
find infrastructure/k8s -name "deployment.yaml" \
  -exec sed -i \
    -e "s|REGISTRY_URL|${REGISTRY}|g" \
    -e "s|IMAGE_TAG|${TAG}|g" \
    {} \;

kubectl apply -f infrastructure/k8s/serviceaccount.yaml
kubectl apply -f infrastructure/k8s/configmap.yaml
kubectl apply -f infrastructure/k8s/mongodb/
kubectl apply -f infrastructure/k8s/redis/
kubectl apply -f infrastructure/k8s/gateway/
kubectl apply -f infrastructure/k8s/ai-service/
kubectl apply -f infrastructure/k8s/avatar-service/
kubectl apply -f infrastructure/k8s/emotion-service/
kubectl apply -f infrastructure/k8s/voice-service/
kubectl apply -f infrastructure/k8s/web-ui/
kubectl apply -f infrastructure/k8s/admin-panel/
kubectl apply -f infrastructure/k8s/ingress.yaml
```

---

## 4. Configurar GitHub Actions (CI/CD automático)

### 4.1 Obter os outputs do Terraform

```bash
cd infrastructure/terraform
terraform output workload_identity_provider
terraform output github_actions_service_account_email
```

### 4.2 Configurar secrets no repositório GitHub

No GitHub → Settings → Secrets and variables → Actions:

| Secret | Valor |
|--------|-------|
| `GCP_PROJECT_ID` | `empathia-462921` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | output do `terraform output workload_identity_provider` |
| `GCP_SERVICE_ACCOUNT` | output do `terraform output github_actions_service_account_email` |

### 4.3 A partir daqui, o deploy é automático

Todo `push` para `main` despoleta o workflow `.github/workflows/deploy.yml` que:
1. Faz build e push das imagens para o Artifact Registry
2. Sincroniza os secrets do Secret Manager para o K8s
3. Aplica os manifests com a nova tag
4. Verifica o rollout

---

## 5. Configurar domínio (DNS)

Após o primeiro deploy, obter o IP do Load Balancer:

```bash
kubectl get ingress empatia-ingress -n empatia
# Aguardar o campo ADDRESS ficar preenchido (pode levar 5-10 minutos)
```

Criar registos DNS no seu provedor:
- `app.empatia.ai` → IP do Ingress
- `admin.empatia.ai` → IP do Ingress

O certificado SSL é provisionado automaticamente pelo GKE Managed Certificate.

---

## 6. Estimativa de custos (us-central1)

| Recurso | Custo estimado/mês |
|---------|-------------------|
| GKE Autopilot (pods) | ~$55–75 |
| Cloud NAT | ~$32 |
| Cloud Load Balancer (Ingress) | ~$18 |
| Artifact Registry | ~$2 |
| Cloud Storage (dados TTS) | ~$1 |
| Secret Manager | ~$0.30 |
| **Total estimado** | **~$108–128/mês** |

> O emotion-service usa Spot Pods (70% desconto), reduzindo ~$15/mês adicionais.
