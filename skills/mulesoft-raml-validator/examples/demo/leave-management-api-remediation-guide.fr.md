# Guide de remédiation — s-leave-management-api

**RAML source :** `examples/demo/leave-management-api.raml`
**RAML corrigé :** `examples/demo/leave-management-api-best-practices.raml`
**Généré le :** 2026-10-25
**Skill :** mulesoft-raml-validator v1.5.0


**API auditée :** Leave Management API (v1.0.3) — couche non déclarée

> Gestion des congés des employés. Les employés déposent leurs demandes de congé (payé, maladie ou sans solde) et en suivent le statut ; les managers les approuvent ; chacun peut consulter le solde de congés restant d'un employé.

6 ressources, 6 opérations · base URI `https://api.demo.jasmineconseil.com/leaves`

---

## 1. Synthèse

Ce guide décrit les transformations appliquées pour corriger le RAML source.
L'audit initial comptait **16 constats** pour un score de
**26/100**. Après ces transformations, le RAML corrigé doit
obtenir **100/100** (à vérifier avec `raml-validator audit` sur le résultat).

**15 transformations** au total :

- 9 **mécaniques** — corrections déterministes et sûres (renommages, mise en forme, insertions structurelles).
- 6 **heuristiques** — valeurs par défaut raisonnables, à relire (exemples provisoires, descriptions générées, URI par défaut).
- 0 **architecturales** — choix de couche ou de nommage pour lesquels plusieurs réponses sont valables.

**Couche API déduite :** `s-` — Couche System (s-) par défaut pour une spécification orientée ressources ; envisager p- ou x- si l'API orchestre ou sert un canal précis.

> ⚠ **6 transformations
> à relire** (choix heuristiques ou architecturaux, ou résultats de confiance
> faible). Chacune est signalée au §3.

---

## 2. Tableau des transformations

| # | Règle | Type | Confiance | Résumé |
|---|---|---|---|---|
| 1 | `NAMING-001` | Mécanique | élevée | /leaveRequests → /leave-requests |
| 2 | `NAMING-002` | Mécanique | élevée | /employee → /employees |
| 3 | `NAMING-003` | Mécanique | élevée | GET /leave-requests?page_size → GET /leave-requests?pageSize |
| 4 | `NAMING-003` | Mécanique | élevée | GET /employees/{employeeId}/balance?page_size → GET /employees/{employeeId}/balance?pageSize |
| 5 | `NAMING-004` | Heuristique | moyenne | title: Leave Management API → title: s-leave-management-api |
| 6 | `VER-002` | Mécanique | élevée | baseUri: https://api.demo.jasmineconseil.com/leaves → baseUri: https://api.demo.jasmineconseil.com/le... |
| 7 | `VER-003` | Mécanique | élevée | version: v1.0.3 → version: v1 |
| 8 | `DOC-002` | Mécanique | élevée | 6 ressources sans description → les 6 ressources ont maintenant une description... |
| 9 | `DOC-003` | Heuristique | moyenne | (aucune section documentation) → documentation: [Overview, Getting started, Error model] |
| 10 | `SEC-001` | Heuristique | moyenne | (aucun securitySchemes, aucun securedBy à la racine) → schéma OAuth 2.0 + securedBy à la racine : [ oa... |
| 11 | `SPEC-003` | Mécanique | élevée | Aucune réponse 4xx/5xx définie sur les points d'accès → trait standardErrors défini et appliqué à 6 méthode(s) |
| 12 | `REUSE-001` | Mécanique | élevée | 2 méthode(s) GET avec page/pageSize en ligne → trait pageable défini et appliqué à 2 méthode(s) |
| 13 | `SPEC-001` | Heuristique | faible — à relire | 1 corps de requête sans exemple → exemples provisoires ajoutés à 1 corps de requête |
| 14 | `SPEC-002` | Heuristique | faible — à relire | 3 corps de réponse sans exemple → exemples provisoires ajoutés à 3 corps de réponse |
| 15 | `SEC-002` | Heuristique | moyenne | 1 point(s) d'accès sensible(s) sans securedBy propre → PUT /users/{userId}/password → scope 'users:cre... |

---

## 3. Transformations détaillées

### 1. `NAMING-001` — Mécanique (élevée)

**Avant :**
```
/leaveRequests
```

**Après :**
```
/leave-requests
```

**Justification :** Les chemins de ressources doivent être en kebab-case (minuscules, séparées par des tirets).


---
### 2. `NAMING-002` — Mécanique (élevée)

**Avant :**
```
/employee
```

**Après :**
```
/employees
```

**Justification :** Les ressources de collection doivent être des noms au pluriel.


---
### 3. `NAMING-003` — Mécanique (élevée)

**Avant :**
```
GET /leave-requests?page_size
```

**Après :**
```
GET /leave-requests?pageSize
```

**Justification :** Les paramètres de requête doivent être en camelCase.


---
### 4. `NAMING-003` — Mécanique (élevée)

**Avant :**
```
GET /employees/{employeeId}/balance?page_size
```

**Après :**
```
GET /employees/{employeeId}/balance?pageSize
```

**Justification :** Les paramètres de requête doivent être en camelCase.


---
### 5. `NAMING-004` — Heuristique (moyenne)

**Avant :**
```
title: Leave Management API
```

**Après :**
```
title: s-leave-management-api
```

**Justification :** Couche déduite : « s- ». Couche System (s-) par défaut pour une spécification orientée ressources ; envisager p- ou x- si l'API orchestre ou sert un canal précis.

> 🔍 **À relire.** La valeur appliquée est générique ; remplacez-la par un
> contenu métier avant la mise en production.

---
### 6. `VER-002` — Mécanique (élevée)

**Avant :**
```
baseUri: https://api.demo.jasmineconseil.com/leaves
```

**Après :**
```
baseUri: https://api.demo.jasmineconseil.com/leaves/{version}
```

**Justification :** Variable {version} insérée dans baseUri pour que les consommateurs figent une version majeure par l'URL.


---
### 7. `VER-003` — Mécanique (élevée)

**Avant :**
```
version: v1.0.3
```

**Après :**
```
version: v1
```

**Justification :** Version de l'URI ramenée au niveau majeur ; mineur et correctif vont dans le changelog et les en-têtes, pas dans l'URL.


---
### 8. `DOC-002` — Mécanique (élevée)

**Avant :**
```
6 ressources sans description
```

**Après :**
```
les 6 ressources ont maintenant une description d'une ligne
```

**Justification :** Descriptions générées : à réécrire avec le sens métier de chaque ressource.


---
### 9. `DOC-003` — Heuristique (moyenne)

**Avant :**
```
(aucune section documentation)
```

**Après :**
```
documentation: [Overview, Getting started, Error model]
```

**Justification :** Section documentation ajoutée avec trois chapitres types : à compléter avec le contenu métier.

> 🔍 **À relire.** La valeur appliquée est générique ; remplacez-la par un
> contenu métier avant la mise en production.

---
### 10. `SEC-001` — Heuristique (moyenne)

**Avant :**
```
(aucun securitySchemes, aucun securedBy à la racine)
```

**Après :**
```
schéma OAuth 2.0 + securedBy à la racine : [ oauth_2_0 ]
```

**Justification :** OAuth 2.0 ajouté avec des URI d'autorisation et de jeton provisoires : à remplacer par celles du fournisseur d'identité avant déploiement.

> 🔍 **À relire.** La valeur appliquée est générique ; remplacez-la par un
> contenu métier avant la mise en production.

---
### 11. `SPEC-003` — Mécanique (élevée)

**Avant :**
```
Aucune réponse 4xx/5xx définie sur les points d'accès
```

**Après :**
```
trait standardErrors défini et appliqué à 6 méthode(s)
```

**Justification :** Un trait unique définit 400/401/403/404/429/500 : chaque méthode a un contrat d'erreur complet.


---
### 12. `REUSE-001` — Mécanique (élevée)

**Avant :**
```
2 méthode(s) GET avec page/pageSize en ligne
```

**Après :**
```
trait pageable défini et appliqué à 2 méthode(s)
```

**Justification :** Paramètres de pagination regroupés dans un trait réutilisable : tout changement de valeur par défaut ou de limite s'applique partout.


---
### 13. `SPEC-001` — Heuristique (faible — à relire)

**Avant :**
```
1 corps de requête sans exemple
```

**Après :**
```
exemples provisoires ajoutés à 1 corps de requête
```

**Justification :** Exemples génériques ajoutés : à remplacer par des valeurs métier réalistes pour rendre le Mocking Service utile.

> 🔍 **À relire.** La valeur appliquée est générique ; remplacez-la par un
> contenu métier avant la mise en production.

---
### 14. `SPEC-002` — Heuristique (faible — à relire)

**Avant :**
```
3 corps de réponse sans exemple
```

**Après :**
```
exemples provisoires ajoutés à 3 corps de réponse
```

**Justification :** Exemples génériques ajoutés : à remplacer par des valeurs métier réalistes.

> 🔍 **À relire.** La valeur appliquée est générique ; remplacez-la par un
> contenu métier avant la mise en production.

---
### 15. `SEC-002` — Heuristique (moyenne)

**Avant :**
```
1 point(s) d'accès sensible(s) sans securedBy propre
```

**Après :**
```
PUT /users/{userId}/password → scope 'users:credentials:write'
```

**Justification :** securedBy ajouté sur chaque point d'accès sensible, avec un scope étroit déduit du chemin : vérifier qu'il existe dans le fournisseur d'identité.

> 🔍 **À relire.** La valeur appliquée est générique ; remplacez-la par un
> contenu métier avant la mise en production.

---

## 4. Prochaines étapes

1. **Relire le RAML corrigé** (`examples/demo/leave-management-api-best-practices.raml`), en particulier les
   6 transformations
   signalées au §3.
2. **Remplacer les valeurs provisoires.** Les descriptions générées (DOC-001,
   DOC-002, DOC-003), les URI d'authentification (SEC-001) et les exemples
   (SPEC-001, SPEC-002) respectent les règles mais n'ont aucun sens métier.
3. **Vérifier les noms de scopes** si SEC-002 a été appliquée. Le générateur les
   déduit du chemin (par ex. `/users/{id}/password` → `users:credentials:write`) ;
   ils doivent exister dans votre fournisseur d'identité.
4. **Refaire l'audit du RAML corrigé** avec `raml-validator audit` pour
   confirmer 100/100 GO. Tout autre résultat est un bug à signaler.
5. **Enregistrer les deux fichiers ensemble** — le RAML corrigé et ce guide,
   qui explique à chaque lecteur futur pourquoi chaque changement a été fait.

---

*Généré par mulesoft-raml-validator v1.5.0 · 2026-10-25 · © 2026 Jasmine Conseil*