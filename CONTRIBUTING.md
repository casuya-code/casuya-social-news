# Contributing to Casuya Social News

Asante kwa kutaka kuchangia! Tunakaribisha michango yote — mafunzo, mawazo, na code.

## Kanuni za Msingi

- **Faili moja = Jukumu moja.** Kila faili inabeba kodi ndogo tu (mistari 30–150).
- Usibadilishe mifumo mingine wakati unarekebisha kosa moja.
- Andika maelezo ya commit wazi na mafupi.
- Usiweke secrets/API keys kwenye repo — zote huenda kwenye `.env`.

## Mchakato wa Michango (Pull Request)

1. **Fork** repo hii.
2. **Clone** fork yako:
   ```bash
   git clone https://github.com/casuya-code/casuya-social-news.git
   cd casuya-social-news
   ```
3. Unda **branch** kwa kazi yako:
   ```bash
   git checkout -b feature/njia-ya-kipengele
   ```
4. Weka `.env` kutoka template:
   ```bash
   cp server-python/.env.example server-python/.env
   ```
5. Funga dependencies na endesha vipimo:
   ```bash
   cd server-python
   pip install -r requirements.txt
   pytest
   ```
6. Endesha linter:
   ```bash
   ruff check .
   ```
7. **Commit** na ujumbe wazi:
   ```bash
   git add .
   git commit -m "feature: ongeza [kipengele]"
   ```
8. **Push** na fungua PR:
   ```bash
   git push origin feature/njia-ya-kipengele
   ```

## Ujumbe wa Commit

Tunatumia conventional commits:

| Prefix | Maana |
|---|---|
| `feature:` | Kipengele kipya |
| `fix:` | Urekebishaji wa kosa |
| `refactor:` | Kupanga upya bila kubadilisha tabia |
| `docs:` | Mabadiliko ya nyaraka tu |
| `test:` | Kuongeza/kurekebisha vipimo |
| `chore:` | Kazi za usimamizi (deps, config) |
| `perf:` | Uboreshaji wa utendaji |
| `security:` | Urekebishaji wa usalama |

## Mfumo wa Vipimo

- Tumia `pytest` kwa moduli za Python.
- Kila moduli hupimwa (unit test) peke yake — hakuna mfumo mzima unaohitajika.
- Endesha vipimo kabla ya kuomba merge.

## Viwango vya Code

- Python 3.12+ na type hints kwa kila function.
- Pydantic models kwa kila request/response.
- JSON logs (structlog) — usitumie print().
- Misimbo inayofuata PEP 8 — `ruff` inaangalia hii.

## Code Review

- Kila PR inakaguliwa na angalau mtu mmoja.
- Tumia review comments kwa maelekezo, si criticism.
- Kazi kubwa (features) igawanywe katika PR ndogo.

## Maswali?

Fungua issue kwenye GitHub au ongea kwenye discussion.