# sqlstruct

SQLModel for [msgspec](https://jcristharif.com/msgspec/).

## Development

Tooling is [uv](https://docs.astral.sh/uv/), [ruff](https://docs.astral.sh/ruff/) and [ty](https://docs.astral.sh/ty/):

```sh
uv sync                 # install dependencies
uv run pytest           # tests
uv run ruff format .    # format
uv run ruff check .     # lint
uv run ty check         # type check
```
