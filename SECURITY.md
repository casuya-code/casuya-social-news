# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| main (dev) | ✅ Supported — hivi vinafuatiliwa |
| Vipi vya awali | ❌ Hatupo kwenye vijiji vyovyote vya awali |

## Kuripoti Udhaifu wa Usalama

**USISITISHE** matatizo ya usalama kwa kufungua issue ya umma kwenye GitHub.

Badala yake, tuma ripoti kwa wahifadhi kwa njia ya faragha:

- Tumia **GitHub Security Advisories** (Recommended): Fungua `Security` → `Report a vulnerability` kwenye repo.
- Au tuma barua pepe kwa wahifadhi kupitia njia ya GitHub.

Usijumuishe:
- API keys halisi
- Data ya kibinafsi
- Manenosiri

## Sera ya Majibu

Tunajitolea:
1. Kuthibitisha kupokelewa kwa ripoti ndani ya **siku 3 za kazi**.
2. Kutoa tathmini ya awali ndani ya **siku 7 za kazi**.
3. Kurekebisha udhaifu na kutoa taarifa ndani ya **siku 30 za kazi** (kutegemea ukubwa).

## Mazingira Salama

Kwa sababu hii ni mfumo unaoshughulikia data ya waandishi wa habari na wahusika:

- **Kamwe** usiweke API keys kwenye repo — zote huenda kwenye `.env` (ambayo imezuiliwa na `.gitignore`).
- Tumia `python-dotenv` kwa secrets.
- API keys za ElevenLabs / Google Cloud / OpenAI **zibadilishwe** mara kwa mara.
- Thibitisha `X-API-Key` kwenye kila request.

## Dependencies

Tunaweka dependencies kwenye `requirements.txt`. Endesha hii mara kwa mara:

```bash
pip install --upgrade -r requirements.txt
pip check
```

## Ripoti za Udhaifu wa Mfumo

Tunashauri watumiaji kuweka dependencies zao zikiwa za kisasa na kufuata mazoea bora ya usalama wa programu.