import logging
import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] [%(request_id)s] %(message)s",
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestIdFilter())


def new_request_id() -> str:
    return uuid.uuid4().hex
