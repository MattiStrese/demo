"""
constants.py
------------
Shared constants used by both app.py and the person-configuration page.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Body-part → muscles mapping (anatomical order: head → feet)
# ---------------------------------------------------------------------------
BODY_PARTS: list[tuple[str, list[str]]] = [
    ("🧠 Nacken", [
        "Sternocleidomastoideus | Splenius Capitis",
    ]),
    ("🫁 Brust", [
        "Pectoralis Clavicularis | Sternalis",
    ]),
    ("🦾 Schulter", [
        "Rotatorenmanschette innen",
        "Rotatorenmanschette aussen",
        "Deltamuskel Vordere Faser",
        "Deltamuskel Mittlere Faser",
        "Deltamuskel Hintere Faser",
        "Trapezius Elevation",
        "Trapezius Retraktion",
        "Trapezius Depression",
    ]),
    ("🔙 Rücken", [
        "Latissimus Dorsi",
        "Serratus Anterior",
    ]),
    ("💪 Oberarme", [
        "Biceps Brachii",
        "Triceps Longum | Lateraler Kopf | Medialer Kopf",
    ]),
    ("🖐 Unterarme", [
        "Finger Flexion",
        "Finger Extension",
        "Handgelenk Flexion",
        "Handgelenk Strecker",
        "Unterarm Supinatoren | Pronatoren",
    ]),
    ("🔥 Core", [
        "Rectus Abdominis",
        "Transversus Abdominis",
        "Obliquus",
        "Erector Spinae",
    ]),
    ("🍑 Hüfte", [
        "Iliopsoas",
        "Gluteus Maximus",
        "Gluteus Medius | Minimus",
        "Gluteus medius (anteriore Fasern)",
        "Adductor Longus | Magnus | Gracilis",
        "Hüft-Außenrotatoren",
    ]),
    ("🦵 Oberschenkel", [
        "Hamstrings",
        "Quadrizeps",
    ]),
    ("🦿 Unterschenkel", [
        "Gastrocnemius | Soleus",
        "Tibialis Anterior",
        "Tibialis Posterior",
    ]),
    ("🦶 Fuß", [
        "Flexor Digitorum Brevis",
        "Extensor Digitorum Brevis",
    ]),
]

# ---------------------------------------------------------------------------
# Movement-theme sets
# ---------------------------------------------------------------------------
FLEXION_MOVEMENTS: set[str] = {"Beugung"}
EXTENSION_MOVEMENTS: set[str] = {"Streckung"}
ROTATION_MOVEMENTS: set[str] = {
    "Rotation", "Lateralflexion", "Adduktion", "Abduktion",
    "Supination", "Pronation", "Elevation", "Depression",
    "Protraktion", "Anti-Extension", "Anti-Rotation", "Inversion",
}

ALL_MOVEMENTS: set[str] = FLEXION_MOVEMENTS | EXTENSION_MOVEMENTS | ROTATION_MOVEMENTS

# Variant keys and their display labels / icons
VARIANTS: list[tuple[str, str, str]] = [
    ("Maschine",    "🏋️", "Maschine"),
    ("HomeGym",     "🏠", "HomeGym"),
    ("Isometrisch", "🧘", "Isometrisch"),
]
