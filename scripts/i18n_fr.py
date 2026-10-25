"""French texts for the reports (v1.4.2) — used when a renderer gets --lang fr.

English stays the default. Rule texts are keyed by rule ID: the French summary
is generic, the location (kept as is) carries the specifics. Generator
reasonings are keyed by their English text; an unknown text is left in English
rather than guessed.
"""

CATEGORIES_FR = {
    "Naming": "Nommage",
    "API-Led Connectivity": "Connectivité API-Led",
    "Reuse": "Réutilisation",
    "Spec": "Spécification",
    "Security": "Sécurité",
    "Versioning": "Versionnement",
    "Documentation": "Documentation",
    "traits / resourceTypes": "traits / resourceTypes",
    "examples / schemas": "exemples / schémas",
}

RULES_FR = {
    "NAMING-001": ("Ressource qui n'est pas en kebab-case.",
                   "URL incohérentes, contraires aux conventions de nommage MuleSoft."),
    "NAMING-002": ("Ressource de collection au singulier : elle doit être un nom au pluriel.",
                   "Un nom de collection au singulier trompe les consommateurs REST qui attendent une liste."),
    "NAMING-003": ("Paramètre de requête qui n'est pas en camelCase.",
                   "Conventions de paramètres incohérentes d'une ressource à l'autre."),
    "NAMING-004": ("Le titre ne suit pas la convention de couche s- / p- / x- en kebab-case.",
                   "Les catalogues API-Led trient par préfixe de couche : l'API ne sera pas identifiée comme System, Process ou Experience dans Anypoint Exchange."),
    "APIC-001": ("Une Experience API expose une ressource de type base de données.",
                 "Le canal consommateur est couplé au stockage : toute évolution du schéma casse le front."),
    "APIC-002": ("Verbe d'orchestration dans une ressource d'une System API.",
                 "L'orchestration relève d'une Process API ; la System API perd son rôle d'accès neutre au système."),
    "APIC-003": ("Le titre ne commence pas par le préfixe de couche (s-, p-, x-).",
                 "La couche de l'API n'est pas identifiable au premier coup d'œil."),
    "REUSE-001": ("Pagination répétée sur plusieurs ressources sans trait commun.",
                  "Chaque changement de pagination doit être reporté à la main partout."),
    "REUSE-003": ("Schéma de sécurité non déclaré à la racine avec securedBy.",
                  "Les méthodes risquent d'être laissées sans protection par oubli."),
    "SPEC-001": ("Corps de requête sans exemple.",
                 "Le Mocking Service et la documentation Exchange restent vides pour ce corps."),
    "SPEC-002": ("Corps de réponse sans exemple.",
                 "Les consommateurs ne voient pas la forme réelle des réponses."),
    "SPEC-003": ("Méthodes sans le jeu complet de réponses d'erreur (400, 401, 404, 500).",
                 "Le contrat d'erreur est incomplet : les clients ne savent pas quoi traiter."),
    "SEC-001": ("Aucun schéma de sécurité et aucun securedBy à la racine : l'API est ouverte.",
                "N'importe qui peut appeler l'API ; bloquant pour une mise en production."),
    "SEC-002": ("Point d'accès sensible sans securedBy explicite.",
                "Une écriture sur une ressource sensible (mot de passe, paiement, utilisateur) n'est pas protégée."),
    "SEC-003": ("OAuth 2.0 est préférable à l'authentification basique en production.",
                "L'authentification basique transmet des secrets réutilisables à chaque appel."),
    "VER-001": ("Pas de champ version à la racine.",
                "Les consommateurs ne peuvent pas suivre ni figer une version de l'API."),
    "VER-002": ("La version n'apparaît pas dans baseUri.",
                "Impossible de faire cohabiter deux versions majeures sur la même URL."),
    "VER-003": ("Version non sémantique dans l'URI (préférer v1, v2).",
                "Les niveaux mineur et correctif n'ont pas leur place dans l'URL."),
    "DOC-001": ("Description racine absente ou de moins de 50 caractères.",
                "Le catalogue Exchange n'explique pas à quoi sert l'API."),
    "DOC-002": ("Ressources sans description.",
                "Les consommateurs doivent deviner le rôle de chaque ressource."),
    "DOC-003": ("Pas de section documentation (présentation, prise en main).",
                "Pas de guide d'intégration pour les nouveaux consommateurs."),
}

REMEDIATION_FR = {
    "NAMING-002": "Mettre le segment au pluriel.",
    "APIC-001": "Retirer la ressource de type base de données et passer par la System API adaptée.",
    "APIC-002": "Exposer l'entité comme un nom (System API) ou extraire cette ressource dans une Process API distincte.",
    "DOC-002": "Ajouter une description d'une ligne sur chaque ressource.",
}

UI_FR = {
    "report_prefix_en": "RAML Audit Report — ",
    "report_prefix_fr": "Rapport d'audit RAML — ",
    "subtitle": "Audit de préparation à la production d'une spécification MuleSoft RAML 1.0",
    "impact": "Impact",
    "remediation": "Correction",
    "occurrences": "{n} occurrences — ",
    "guide_prefix_en": "Remediation guide — ",
    "guide_prefix_fr": "Guide de remédiation — ",
}

KIND_LABEL_FR = {"mechanical": "Mécanique", "heuristic": "Heuristique",
                 "architectural": "Architecturale"}
CONFIDENCE_LABEL_FR = {"high": "élevée", "medium": "moyenne",
                       "low": "faible — à relire"}

REASONING_FR = {
    "Resource paths must be kebab-case (lowercase, hyphen-separated).":
        "Les chemins de ressources doivent être en kebab-case (minuscules, séparées par des tirets).",
    "Collection resources must be plural nouns.":
        "Les ressources de collection doivent être des noms au pluriel.",
    "Query parameters must be camelCase.":
        "Les paramètres de requête doivent être en camelCase.",
    ("Orchestration verbs in resource paths belong to a Process API. "
     "Renamed to a noun form. If this is a System API, consider extracting "
     "the orchestration to a separate Process API instead of just renaming."):
        ("Un verbe d'orchestration dans un chemin relève d'une Process API. Renommé "
         "en nom. S'il s'agit d'une System API, envisagez plutôt d'extraire "
         "l'orchestration dans une Process API distincte."),
    "Auto-generated placeholder description meeting the 50-char minimum. Edit to describe the actual API.":
        "Description provisoire générée pour atteindre 50 caractères : à remplacer par la description réelle de l'API.",
    "Auto-generated descriptions; edit them to capture domain-specific intent.":
        "Descriptions générées : à réécrire avec le sens métier de chaque ressource.",
    "Skeleton documentation section added with three standard chapters. Edit each chapter to add domain-specific content.":
        "Section documentation ajoutée avec trois chapitres types : à compléter avec le contenu métier.",
    "Version placeholder interpolated so consumers can pin to a major version via the URL.":
        "Variable {version} insérée dans baseUri pour que les consommateurs figent une version majeure par l'URL.",
    "URI version reduced to major level; patch/minor levels belong in the changelog and response headers, not the URL.":
        "Version de l'URI ramenée au niveau majeur ; mineur et correctif vont dans le changelog et les en-têtes, pas dans l'URL.",
    "OAuth 2.0 added with placeholder authorization/token URIs. Replace these with the real identity-provider URLs before deploying.":
        "OAuth 2.0 ajouté avec des URI d'autorisation et de jeton provisoires : à remplacer par celles du fournisseur d'identité avant déploiement.",
    "Scoped securedBy added per sensitive endpoint with a narrow scope inferred from the path. Verify the scope name matches your identity-provider configuration.":
        "securedBy ajouté sur chaque point d'accès sensible, avec un scope étroit déduit du chemin : vérifier qu'il existe dans le fournisseur d'identité.",
    "Single trait defining 400/401/403/404/429/500 ensures every method has a complete error contract.":
        "Un trait unique définit 400/401/403/404/429/500 : chaque méthode a un contrat d'erreur complet.",
    "Pagination parameters factored into a single reusable trait; future changes to defaults or limits propagate everywhere.":
        "Paramètres de pagination regroupés dans un trait réutilisable : tout changement de valeur par défaut ou de limite s'applique partout.",
    "Generic placeholder examples added; replace with realistic domain-specific values to make Mocking Service useful.":
        "Exemples génériques ajoutés : à remplacer par des valeurs métier réalistes pour rendre le Mocking Service utile.",
    "Generic placeholder examples added; replace with realistic domain-specific values.":
        "Exemples génériques ajoutés : à remplacer par des valeurs métier réalistes.",
}

LAYER_REASONING_FR = [
    ("Title already declares layer prefix", "Le titre déclare déjà le préfixe de couche."),
    ("Resources contain orchestration verbs",
     "Les ressources contiennent des verbes d'orchestration : la couche Process est la plus adaptée."),
    ("Default to System (s-) layer",
     "Couche System (s-) par défaut pour une spécification orientée ressources ; envisager p- ou x- si l'API orchestre ou sert un canal précis."),
]


def layer_reasoning_fr(text: str) -> str:
    for start, fr in LAYER_REASONING_FR:
        if text.startswith(start):
            return fr
    return text


def reasoning_fr(text: str) -> str:
    if text.startswith("Layer inferred: '"):
        layer = text.split("'")[1]
        rest = text.split(". ", 1)[1] if ". " in text else ""
        return f"Couche déduite : « {layer} ». {layer_reasoning_fr(rest)}"
    return REASONING_FR.get(text, text)
