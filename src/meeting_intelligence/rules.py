from __future__ import annotations

import re

UNIVERSAL_SEEDS: dict[str, tuple[str, ...]] = {
    "NEGATION": (r"\bno\b", r"\bnunca\b", r"\btampoco\b", r"\bsin\b"),
    "ADVERSATIVE": (r"\bpero\b", r"\bsin embargo\b", r"\baunque\b", r"\bno obstante\b"),
    "CONCERN": (r"\bpreocupa\w*\b", r"\binquiet\w*\b", r"\btemor\w*\b", r"\bproblema\w*\b"),
    "RISK": (r"\briesgo\w*\b", r"\bimpacto\w*\b", r"\bcritic\w*\b", r"\bfall\w*\b", r"\bafectar\w*\b"),
    "CONSTRAINT": (r"\bimposible\b", r"\bno podemos\b", r"\bno se puede\b", r"\bno hay forma\b"),
    "SCOPE": (r"\balcance\b", r"\bfuera de\b", r"\bfase\b", r"\bcontratad\w*\b", r"\bcobertura\b"),
    "OBLIGATION": (r"\bnecesitamos\b", r"\bdebe\w*\b", r"\btiene\w* que\b", r"\bes necesario\b"),
    "UNCERTAINTY": (r"\bno se si\b", r"\bprobablemente\b", r"\ba lo mejor\b", r"\bcreo que\b"),
    "ALIGNMENT": (r"\bde acuerdo\b", r"\bperfecto\b", r"\baprob\w*\b", r"\bacord\w*\b"),
}

PRODUCTIVE_TEMPLATES: dict[str, str] = {
    "NO_MODAL_VERB": r"\bno\s+(?:va(?:n)?\s+a\s+)?(?:podemos|puede(?:n)?|poder|funciona(?:r)?|cubre|cubrir|abarca(?:r)?|permite|existe|tenemos|hay)\b",
    "DIRECT_CONCERN": r"\b(?:me|nos)\s+preocupa(?:\s+(?:mucho|enormemente))?\b",
    "REPORTED_CONCERN": r"\b(?:entiendo|comprendo|reconozco)\s+(?:tu|su|la)\s+preocupacion\b",
    "OMISSION_RESULT": r"\b(?:se|nos)\s+(?:van\s+a\s+)?quedar\w*\b.{0,100}\b(?:fuera|por fuera|incomplet\w*)\b",
    "SCOPE_EXCLUSION": r"\b(?:no\s+esta|queda)\b.{0,80}\b(?:contratad\w*|dentro del alcance|fuera de alcance)\b",
    "TIME_PRESSURE": r"\b(?:poco tiempo|plazo insuficiente|imposible|no vamos a lograrlo|retrasar el proyecto)\b",
    "VENDOR_ESCALATION": r"\b(?:contratar|buscar|traer)\b.{0,80}\b(?:otra consultora|otro consultor|otro proveedor)\b",
    "CLARIFICATION_PRESSURE": r"\b(?:lo que quiero entender|lo que quiero dejar claro|volvemos a la pregunta|necesito una respuesta clara)\b",
    "SYSTEM_LIMITATION": r"\b(?:el sistema|la plataforma|el erp)\b.{0,60}\b(?:no hace|no permite|no puede|no cubre|no tiene)\b",
    "AGREEMENT": r"\b(?:queda acordado|se acuerda|queda aprobado|la decision es|procederemos de esta manera)\b",
    "COMMITMENT": r"\b(?:yo envio|yo preparo|me encargo|nos encargamos|lo tendremos|vamos a entregar)\b",
}

NEGATIVE_LEXICON: dict[str, float] = {
    "preocupa": 2.8,
    "preocupacion": 2.5,
    "inquietud": 2.1,
    "problema": 1.5,
    "problemas": 1.5,
    "imposible": 3.0,
    "riesgo": 1.7,
    "riesgos": 1.7,
    "critico": 2.2,
    "critica": 2.2,
    "fracaso": 3.0,
    "falla": 2.3,
    "quiebra": 3.2,
    "atrasar": 2.0,
    "afectar": 1.5,
    "dificil": 1.1,
    "falta": 1.0,
}

POSITIVE_LEXICON: dict[str, float] = {
    "perfecto": 2.3,
    "acuerdo": 1.8,
    "alineados": 1.8,
    "tranquilos": 1.7,
    "feliz": 2.3,
    "gracias": 0.7,
    "bueno": 0.7,
    "mejor": 0.9,
    "aprobacion": 1.4,
    "satisfacer": 1.4,
}

INTENSIFIERS: dict[str, float] = {
    "enormemente": 1.55,
    "demasiado": 1.35,
    "totalmente": 1.30,
    "definitivamente": 1.30,
    "muy": 1.18,
    "muchisimo": 1.30,
    "critico": 1.30,
    "critica": 1.30,
    "imposible": 1.45,
}

HYPOTHETICAL_RE = re.compile(
    r"\b(?:por ejemplo|es un ejemplo|a modo de ejemplo|si ustedes me dicen|supongamos|imaginemos)\b",
    re.IGNORECASE,
)
HEDGE_RE = re.compile(
    r"\b(?:a lo mejor|probablemente|es probable|creo que|puede ser|podria|posiblemente|no se si)\b",
    re.IGNORECASE,
)
