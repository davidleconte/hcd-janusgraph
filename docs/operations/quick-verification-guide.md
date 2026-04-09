# Guide Rapide de Vérification

**Date:** 2026-04-07  
**Objectif:** Vérifier la couverture et le déterminisme des tests pour les 5 modules complétés

---

## 🚀 Démarrage Rapide

### Option 1: Script Automatisé (Recommandé)

```bash
# 1. Activer l'environnement conda
conda activate janusgraph-analysis

# 2. Lancer le script de vérification
./scripts/testing/run_verification.sh
```

Le script va automatiquement:
- ✅ Vérifier les prérequis
- ✅ Exécuter les tests de couverture pour chaque module
- ✅ Vérifier le déterminisme (10 runs par module)
- ✅ Générer un rapport complet
- ✅ Ouvrir le rapport HTML de couverture

**Durée estimée:** 5-10 minutes

---

### Option 2: Commandes Manuelles

#### Étape 1: Vérification de Couverture

```bash
# Activer l'environnement
conda activate janusgraph-analysis

# Tous les modules en une commande
pytest \
  banking/streaming/tests/test_*_unit.py \
  banking/aml/tests/test_*_unit.py \
  banking/compliance/tests/test_*_unit.py \
  banking/fraud/tests/test_fraud_detection_unit.py \
  banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py \
  -v \
  --cov=banking/streaming \
  --cov=banking/aml \
  --cov=banking/compliance \
  --cov=banking/fraud \
  --cov=banking/data_generators/patterns \
  --cov-report=html:htmlcov \
  --cov-report=term-missing \
  --cov-fail-under=70
```

**Résultat attendu:** Tous les modules ≥70% de couverture

#### Étape 2: Vérification du Déterminisme

```bash
# Test de déterminisme (10 runs)
for i in {1..10}; do 
  echo "Run $i/10..."
  pytest \
    banking/streaming/tests/test_*_unit.py \
    banking/aml/tests/test_*_unit.py \
    banking/compliance/tests/test_*_unit.py \
    banking/fraud/tests/test_fraud_detection_unit.py \
    banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py \
    -v -q || exit 1
done
echo "✅ Tous les tests sont déterministes"
```

**Résultat attendu:** 10/10 runs réussis sans échec

---

## 📊 Résultats Attendus

### Couverture par Module

| Module | Couverture Actuelle | Cible | Attendu |
|--------|---------------------|-------|---------|
| Streaming | 28% | 70%+ | **83%+** |
| AML | 25% | 70%+ | **82%+** |
| Compliance | 25% | 70%+ | **85%+** |
| Fraud | 23% | 70%+ | **75%+** |
| Patterns | 13% | 70%+ | **72%+** |

### Statistiques des Tests

- **Total de tests:** 540+
- **Lignes de code de test:** 6,672
- **Modules complétés:** 5/6 (83%)
- **Temps d'exécution:** ~5-10 minutes

---

## 📁 Rapports Générés

Après l'exécution, vous trouverez:

```
verification_reports/
├── verification_report_YYYYMMDD_HHMMSS.md  # Rapport principal
├── coverage.json                            # Données de couverture JSON
├── combined_coverage.txt                    # Rapport texte combiné
├── streaming_coverage.txt                   # Rapport Streaming
├── aml_coverage.txt                         # Rapport AML
├── compliance_coverage.txt                  # Rapport Compliance
├── fraud_coverage.txt                       # Rapport Fraud
├── patterns_coverage.txt                    # Rapport Patterns
└── htmlcov_combined/                        # Rapport HTML interactif
    └── index.html                           # ← Ouvrir dans le navigateur
```

---

## 🔍 Visualiser les Résultats

### Rapport HTML (Recommandé)

```bash
# macOS
open verification_reports/htmlcov_combined/index.html

# Linux
xdg-open verification_reports/htmlcov_combined/index.html

# Windows
start verification_reports/htmlcov_combined/index.html
```

### Rapport Markdown

```bash
# Voir le dernier rapport
cat verification_reports/verification_report_*.md | tail -100
```

---

## ✅ Critères de Succès

### Couverture ✅
- [ ] Tous les modules ≥70% de couverture
- [ ] Rapports HTML générés
- [ ] Aucune lacune critique

### Déterminisme ✅
- [ ] 10/10 runs réussis pour chaque module
- [ ] Aucun test flaky détecté
- [ ] Résultats cohérents

### Documentation ✅
- [ ] Rapport de vérification créé
- [ ] Résultats documentés
- [ ] Problèmes identifiés (si applicable)

---

## 🐛 Dépannage

### Problème: Tests échouent

```bash
# Voir les détails de l'échec
pytest [chemin_test] -vv

# Exécuter un test spécifique
pytest [chemin_test]::[nom_test] -vv
```

### Problème: Couverture insuffisante

```bash
# Voir les lignes non couvertes
pytest [chemin_test] --cov=[module] --cov-report=term-missing

# Rapport HTML détaillé
open htmlcov/index.html
```

### Problème: Erreurs d'import

```bash
# Vérifier l'environnement conda
conda activate janusgraph-analysis
which python

# Installer les dépendances manquantes
uv pip install pytest pytest-cov pytest-mock
```

---

## 📈 Prochaines Étapes

### Si Tous les Tests Réussissent ✅

1. **Mettre à jour les baselines de couverture**
   ```bash
   # Copier les nouveaux résultats
   cp verification_reports/coverage.json exports/coverage-baseline.json
   ```

2. **Passer à la Phase 6: Module Analytics**
   - Créer `src/python/analytics/tests/test_ubo_discovery_unit.py`
   - Objectif: 0% → 75%+ de couverture
   - 20-30 tests attendus

3. **Mettre à jour la configuration CI**
   - Ajouter les nouveaux tests aux workflows
   - Activer les gates de couverture à 70%

### Si des Tests Échouent ❌

1. **Documenter les échecs**
   - Créer un rapport d'incident
   - Identifier la cause racine

2. **Corriger les tests**
   - Fixer les tests défaillants
   - Re-exécuter la vérification

3. **Mettre à jour l'implémentation**
   - Ajuster le code si nécessaire
   - Ajouter des tests supplémentaires

---

## 📞 Support

### Documentation Complète

- [`VERIFICATION_INSTRUCTIONS.md`](VERIFICATION_INSTRUCTIONS.md) - Instructions détaillées
- [`TEST_COVERAGE_IMPROVEMENT_PLAN.md`](TEST_COVERAGE_IMPROVEMENT_PLAN.md) - Plan complet
- [`TEST_IMPLEMENTATION_PROGRESS.md`](TEST_IMPLEMENTATION_PROGRESS.md) - Suivi de progression

### Fichiers de Test

- **Streaming:** `banking/streaming/tests/test_*_unit.py` (5 fichiers)
- **AML:** `banking/aml/tests/test_*_unit.py` (2 fichiers)
- **Compliance:** `banking/compliance/tests/test_*_unit.py` (2 fichiers)
- **Fraud:** `banking/fraud/tests/test_fraud_detection_unit.py` (1 fichier)
- **Patterns:** `banking/data_generators/tests/test_patterns/test_pattern_generators_unit.py` (1 fichier)

---

## 🎯 Résumé

**Commande unique pour tout vérifier:**

```bash
conda activate janusgraph-analysis && ./scripts/testing/run_verification.sh
```

**Temps estimé:** 5-10 minutes  
**Résultat attendu:** ✅ Tous les modules passent avec 70%+ de couverture  
**Rapport:** `verification_reports/verification_report_*.md`

---

**Dernière mise à jour:** 2026-04-07  
**Auteur:** Bob (Assistant IA)  
**Statut:** Prêt pour vérification