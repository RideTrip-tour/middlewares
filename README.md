# internal-middleware

FastAPI middleware для извлечения user context из заголовков
`X-User-Claims` и `X-User-ID`, а также идентификатора запроса `X-Request-ID`.

## Установка

В `pyproject.toml` сервиса:

```toml
dependencies = [
    "internal-middleware @ git+ssh://github.com/RideTrip-tour/middlewares.git@<tag>",
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


logger = logging.getLogger("my-service")


app.middleware("http")(
    build_request_id_middleware(logger=logger)
)

app.middleware("http")(
    build_user_context_middleware(
        logger=logging.getLogger(logger=logger),
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

## Параметры фабрики `build_user_context_middleware`

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


## Параметры фабрики `build_request_id_middleware`

| Параметр | По умолчанию | Описание |
|---|---|---|
| `logger` | `logging.getLogger(__name__)` | Логгер сервиса |
| `header_name` | `"X-Request-ID"` | Заголовок с идентификатором запроса |

### Поведение

- Если `X-Request-ID` передан и соответствует допустимому формату - используется полученное значение.
- Если заголовок отсутствует или содержит недопустимое значение - генерируется новый UUID4.
- Идентификатор сохраняется в `request.state.request_id`.
- Идентификатор устанавливается в `request_id_var` на время обработки запроса.
- В ответ добавляется заголовок `X-Request-ID` с тем же идентификатором.
- После завершения обработки запроса контекст сбрасывается через `ContextVar.reset()`.
- При исключениях контекст также сбрасывается.
