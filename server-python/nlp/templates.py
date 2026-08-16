"""Drama template data: cast, dialogue lines, proverbs, slang.

Separated from the contextualizer so the generation logic stays clean and
the data can be imported independently by tests or other modules.
"""

from __future__ import annotations

# The core cast — two speakers per scene for the MVP.
CAST: list[dict[str, str]] = [
    {"id": "char_bibi_mkwe", "name": "Bibi Mkwe", "voice_id": "mock_bibi", "mood": "uchangamfu"},
    {"id": "char_mjomba", "name": "Mjomba Juma", "voice_id": "mock_mjomba", "mood": "hasira"},
    {"id": "char_rafiki", "name": "Rafiki Neema", "voice_id": "mock_neema", "mood": "msisimko"},
]

OPENINGS = [
    "Hujasikia? Mambo yameendelea leo!",
    "Wewe, leo kuna habari kubwa!",
    "Ngoja nikuambie kilichotokea...",
]

MEMORY_OPENINGS = [
    "Kumbuka tulichokizungumzia jana... sasa inaendelea!",
    "Hii ni mwendelezo wa habari tuliyoiona hapo awali.",
    "Unakumbuka tulivyozungumza? Leo imekuwa kubwa zaidi.",
]

REACTIONS_NEUTRAL = [
    "Haiwezekani! Kweli ndivyo ilivyo?",
    "Nashangaa sana kusikia hivyo.",
    "Mh... hii inabadilisha mambo mengi.",
    "Lakini sasa, hii ni hatari kweli.",
]

REACTIONS_WORRIED = [
    "Hii inatia wasiwasi sana. Tunaweza kufanya nini?",
    "Sidhani kama tutajisikia vizuri na habari kama hii.",
    "Mh... wakati mgumu unakuja. Tunahitaji kuwa makini.",
]

REACTIONS_UPBEAT = [
    "Hii ni nzuri sana! Kila mtu akusanye habari hii!",
    "Nimefurahi sana! Tumekuwa tukingojea hii kwa muda.",
    "Kesho watu wote watakuwa wakizungumza kuhusu hii!",
]

CLOSINGS = [
    "Basi, tunaendelea kuona mambo yatakavyokuja.",
    "Tunafuatilia hadithi hii kwa makini.",
    "Na ndivyo ilivyokuwa leo, tusubiri kesho.",
]

# Direction-tuned closings (Feature #35): the community's chosen direction
# shapes how the scene resolves.
CLOSINGS_BY_DIRECTION = {
    "msisimko": [
        "Na kitu kinachofuata kinaweza kuwa kubwa! Subiri tu.",
        "Msisimko umezidi! Tutakuambia kinachotokea baadaye.",
        "Hii ndiyo mwanzo tu wa mambo makubwa yanayokuja!",
    ],
    "furaha": [
        "Hii inaleta matumaini makubwa kwa siku zijazo!",
        "Tunaweza kufurahi leo; habari nzuri imefika!",
        "Ni siku njema! Tumefurahishwa na mwendo huu.",
    ],
    "wasiwasi": [
        "Tunahitaji kuwa makini sana; mambo bado yanaendelea.",
        "Wasiwasi unaongezeka; tutafuatilia kwa karibu.",
        "Huu ni wakati wa kujiandaa kwa yale yanayokuja.",
    ],
    "utulivu": [
        "Basi, tulia na tusubiri maelezo zaidi.",
        "Tunachukua muda kuangalia mambo kwa utulivu.",
        "Hakuna haraka; tukusanye ukweli kwanza.",
    ],
}

# Feature #1: narrative prompts — methali (proverbs) woven into dialogue.
PROVERBS = [
    "Haraka haraka haina baraka.",
    "Mvumilivu hula mbivu.",
    "Kidole kimoja hakivunji chawa.",
    "Mwacha mila ni mtumwa.",
    "Polepole ndiyo mwendo.",
    "Asiyekujua hakuthamini.",
    "Mtaka yote hukosa yote.",
    "Haba na haba hujaza kibaba.",
]

# Feature #26: slang dictionary — lightweight urban Swahili layer.
SLANG = {
    "opening": ["Mambo!", "Vipi, kijana?", "Mkuu, unasikia?", "Jambo! Usikilize hii."],
    "filler": ["mpaka nini?", "basi na basi.", "sasa hivi tu.", "niliyaona mato!"],
}

SLANG_OPENINGS = [
    "Mkuu, kuna jambo la moto!",
    "Mambo! Habari kubwa imefika leo!",
    "Ngoja nikwambie, hii ni kubwa sana!",
]
