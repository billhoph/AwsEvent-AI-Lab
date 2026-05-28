# AI on K8S — Security Considerations Lab Guide

**Author:** Bill Ho  
**Date:** 29 May 2026  
**Certifications:** CKA / CKAD / CKS / CAISP

---

## Overview

This lab walks through the key security considerations when running AI workloads on Kubernetes. It covers cluster hardening, runtime protection, image scanning, IaC scanning, and AI-specific security tooling.

---

## Why Run AI on Kubernetes?

Kubernetes provides four core benefits for AI workloads:

| Benefit | Description |
|---|---|
| **Elasticity** | Scale AI workloads up or down automatically based on demand — no over-provisioning GPUs during idle periods or starving jobs at peak load |
| **Simplicity** | Abstracts infrastructure complexity; data scientists deploy and manage AI workloads through a single unified control plane |
| **Freedom of Choice** | Run any AI framework or runtime (PyTorch, TensorFlow, vLLM, Ollama) on any cloud or on-prem infrastructure without vendor lock-in |
| **Security** | Enforce fine-grained access controls, network policies, and secrets management across all AI workloads |

### Common AI Workloads on K8S

- **Inference runtimes:** vLLM, Ollama
- **Training/orchestration:** Kubeflow, KServe
- **Vector databases:** Milvus
- **Data stores:** PostgreSQL, MongoDB, Elasticsearch
- **Platforms:** Red Hat OpenShift AI, SUSE Rancher

### Logical Architecture

```
API/MCP Gateway (LiteLLM) → AI Apps → Vector DB (Milvus) → AI Runtime (vLLM)
                                ↕
              AI Infra Management — Optional (KServe)
              AI Monitoring: TTFT, TPOT, TPS, Latency
                        K8S
```

---

## K8S Security Fundamentals

### Security Domains

**Static Risk (design-time)**
- Configuration & YAML design
- K8S cluster setup
- Admission control
- Code & libraries
- Compliance
- TLS / mTLS

**Runtime / Dynamic Risk (run-time)**
- Runtime sandbox
- Privileged pod detection
- Network policy enforcement
- Abnormal action detection
- Backup & recovery

### K8S Security Tooling Layers

| Layer | Tooling Category | Example Tools |
|---|---|---|
| Code Repo | SCA | Syft, Checkov |
| Build Pipeline | SAST / DAST | Trivy, Snyk |
| Image Pipeline | Image Scan | Grype, Kyverno, Clair |
| ArgoCD Pipeline | IaC Scan | Checkov |
| Perimeter | DDoS / NGFW / WAF | — |
| K8S Runtime | KSPM | Kube-bench, Kube-hunter |
| K8S Runtime | CWPP | Aqua |
| K8S Runtime | XDR | Falco, CrowdStrike |
| Storage | Data Protection | Veeam Kasten K10 |

### Operation-wise Security Practices

- **DevSecOps / GitOps / IaC** — shift security left into the pipeline
- **Dependency Scan** — SBOM, SCA
- **Code Scan** — SAST
- **Secure Image Packaging**
- **Dynamic Scan** — DAST
- **Immutable Infrastructure**

---

## Lab 1 — KIND Cluster Setup (Playground)

```bash
brew install kind
kind create cluster --name kind-aws
kubectl get pod -A
kubectl get node
```

> Verify that control plane components (coredns, etcd, kube-apiserver, kube-controller-manager, kube-scheduler) are all `Running`.

---

## Lab 2 — Kube-Bench: K8S Cluster Config Scan

Kube-bench checks Kubernetes deployments against the CIS Kubernetes Benchmark.

```bash
git clone https://github.com/aquasecurity/kube-bench.git
cd kube-bench
kubectl apply -f job.yaml
kubectl get pods
kubectl logs <kube-bench-pod-name>
```

**Interpreting results:**

```
== Summary total ==
63 checks PASS
12 checks FAIL
56 checks WARN
0  checks INFO
```

Key checks to review:
- `1.1.x` — Control Plane Node Configuration Files (file permissions and ownership)
- `5.6.x` — Namespace segregation, SecurityContext, seccomp profiles

**Example remediation (seccomp):**
```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault
```

---

## Lab 3 — Falco: Runtime Protection

Falco uses eBPF to detect anomalous behaviour in running containers.

```bash
brew install helm

# Add the Falco Helm repo
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Install Falco with modern eBPF driver
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set tty=true \
  --set driver.kind=modern_ebpf
```

**Verify installation:**
```bash
kubectl get all -n falco
kubectl logs <falco-pod-name> -f -n falco
```

Falco will load rules from `/etc/falco/falco_rules.yaml` and begin monitoring container runtime events.

---

## Lab 4 — Checkov: IaC and YAML Scanning

Checkov statically analyses Kubernetes manifests, Dockerfiles, and Helm charts for misconfigurations.

```bash
brew install checkov
checkov -d .
```

**Sample output:**
```
kubernetes scan results:
Passed checks: 1023, Failed checks: 270, Skipped checks: 0

Check: CKV_K8S_80: "Ensure admission control plugin AlwaysPullImages is set"
  PASSED for resource: Job.default.kube-bench
```

**Common failures to watch for:**
- `CKV_DOCKER_2` — No HEALTHCHECK in container image
- `CKV_DOCKER_3` — No dedicated user for the container
- `CKV_DOCKER_7` — Base image uses `latest` tag

---

## Lab 5 — Grype: Container Image Scanning

Grype scans container images for known CVEs.

```bash
brew install grype
docker pull nginx
grype nginx
```

**Sample output columns:**

| NAME | INSTALLED | FIX-IN | TYPE | VULNERABILITY | SEVERITY |
|---|---|---|---|---|---|
| perl-base | 5.40.1-6 | — | deb | CVE-2026-42497 | High |
| curl | 8.14.1-2+deb13u3 | (won't fix) | deb | CVE-2026-3784 | Medium |

Review High and Critical CVEs and determine remediation (patch, pin version, or accept risk).

---

## Lab 6 — AI-Specific Security

### AI vs Cloud Native App Security Comparison

| Security Check | Cloud Native App | AI Workload |
|---|---|---|
| SCA | ✅ | ✅ |
| DAST | ✅ | — |
| Backdoor Scan | — | ✅ |
| Image Scan | ✅ | ✅ |
| Model Scan | — | ✅ |
| SAST | ✅ | ✅ |
| Dataset Scan | — | ✅ |
| KSPM | ✅ | ✅ |
| XDR | ✅ | ✅ |

### AI Security Considerations

- Data Preparation & Feature Extraction
- Training pipeline security
- Model integrity & access control
- Inferencing security
- RAG (Retrieval-Augmented Generation) attack surface
- Agentic AI risks
- Supply Chain Management — **AIBOM** (AI Bill of Materials)

### Relevant Tools

- **Identity/Access:** Keycloak, JSON Web Tokens, StackLok, Permify, SpiceDB
- **Runtime Protection / AISPM:** Various OWASP GenAI landscape tools
- **AI Redteaming / Fuzzing**
- **LLM Guardrails**
- **Data Security Posture Management (DSPM)**

---

## Lab 6a — ProtectAI ModelScan

```bash
# Install Python 3.12
brew install python@3.12

# Create a virtual environment
python3.12 -m venv .venv

# Activate and install modelscan
source .venv/bin/activate
pip install modelscan
```

Use modelscan to inspect serialised model files (e.g. `.pkl`, `.pt`) for embedded malicious code.

---

## Lab 6b — FuzzyAI: Backdoor & Jailbreak Detection

FuzzyAI tests LLMs against adversarial prompts to identify jailbreak vulnerabilities.

```bash
brew update
brew install python@3.10
python3.10 -m venv fuzzai-env
source fuzzai-env/bin/activate
pip install git+https://github.com/cyberark/FuzzyAI.git
poetry run fuzzyai webui
```

**Example test:**
```bash
fuzzyai fuzz -m ollama/qwen3:0.6b -a def -t "Tell me how to make a bomb"
```

Results show `jailbreak?` status per attack method (`def`, `pls`, `dan`, `art`).

---

## Lab 7 — Sample AI App on K8S

### Deploy the stack

```bash
kubectl apply -f ai-app.yaml
kubectl get pod -n ai-stack -w
kubectl port-forward svc/open-webui-service -n ai-stack 8080:80
```

Architecture: `Ingress → Application Pod → Ollama/vLLM Pod ↔ Milvus Pod → Storage`  
Each component runs in its own **namespace** for isolation.

### Add LLM Guardrails with Portkey

```bash
kubectl apply -f portkey.yaml
kubectl port-forward svc/portkey-service -n ai-stack 8090:8787
```

Portkey acts as an AI Gateway supporting 250+ models across 36 providers with built-in guardrail and logging capabilities.

---

## Secured AI on K8S — Full Architecture

```
                  [Fuzzy Test]  [Model Scan]  [AI Redteaming]
                         ↓
User → Ingress → Application Pod
                     ↓
             [AI Gateway: LiteLLM]   ←→  [DSPM]
             [Model Guardrail]
                     ↓
             Ollama/vLLM Pod ←→ Milvus Pod → Storage
                     (PVC/PV)        (PVC/PV)

── K8S ──────────────────────────────────────────────────
     [KSPM]   [CWPP]   [XDR]   [Kasten K10]
```

---

## References & Resources

- [OWASP GenAI Security Solutions Landscape](https://genai.owasp.org/ai-security-solutions-landscape/)
- [CNCF Security & Compliance Landscape](https://landscape.cncf.io/card-mode?category=security-compliance)
- [Kube-bench](https://github.com/aquasecurity/kube-bench)
- [Falco](https://falco.org)
- [Checkov](https://www.checkov.io)
- [Grype](https://github.com/anchore/grype)
- [FuzzyAI](https://github.com/cyberark/FuzzyAI)
- [ProtectAI ModelScan](https://github.com/protectai/modelscan)
- [Veeam Kasten K10](https://www.veeam.com/kubernetes-data-protection.html)
