# internal-middleware

FastAPI middleware для извлечения user context из заголовков
`X-User-Claims` и `X-User-ID`.

## Установка

В `pyproject.toml` сервиса:

```toml
dependencies = [
    "internal-middleware @ git+ssh://git@github.com/RideTrip-tour/internal_middleware.git@v0.1.0",
]
```

Затем:

```bash
pip install -e .
# или
poetry install
# или
uv sync
```

## Проверка
После установки проверьте, что библиотека импортируется:

```bash
python -c "import internal_middleware; print(internal_middleware.__file__)"
```

Если команда завершилась без ошибок, библиотека доступна в текущем Python-окружении.

## Использование

В `app/main.py` сервиса:

```python
import logging
from internal_middleware import build_user_context_middleware

app.middleware("http")(
    build_user_context_middleware(
        logger=logging.getLogger("my-service"),
    )
)
```

В хендлерах:

```python
from internal_middleware import user_claims

@app.get("/me")
async def me():
    claims = user_claims.get()
    return {"user_id": claims.get("user_id")}
```

## Параметры фабрики

| Параметр | По умолчанию | Описание |
|---|---|---|
| `logger` | `logging.getLogger(__name__)` | Логгер сервиса |
| `claims_header` | `"x-user-claims"` | Заголовок с base64url-JSON |
| `user_id_header` | `"x-user-id"` | Заголовок с user_id |

## Поведение

- Если `X-User-Claims` есть — используется он, `X-User-ID` игнорируется.
- Если только `X-User-ID` — используется он (число парсится как int).
- Если ничего нет — `user_claims.get()` вернёт `{}`.
- Если заголовок битый — ответ 401 `{"detail": "Unauthorized"}`.