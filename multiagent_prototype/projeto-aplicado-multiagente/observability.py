"""
Setup de observabilidade com OpenTelemetry.

Exporta spans para o console (visível no terminal) e persiste em
evidence/traces.json. Em produção, basta substituir o ConsoleSpanExporter
por OTLPSpanExporter apontando para Jaeger/Tempo.

Referência: ADR #003.
"""
import json
import os
from datetime import datetime
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.sdk.resources import Resource


EVIDENCE_DIR = Path(__file__).parent / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)
TRACES_FILE = EVIDENCE_DIR / "traces.json"


class JSONFileSpanExporter(SpanExporter):
    """Exporter que persiste spans como JSON, para uso como evidência."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._spans: list[dict] = []

    def export(self, spans) -> SpanExportResult:
        for span in spans:
            ctx = span.get_span_context()
            self._spans.append({
                "name": span.name,
                "trace_id": format(ctx.trace_id, "032x"),
                "span_id": format(ctx.span_id, "016x"),
                "parent_id": format(span.parent.span_id, "016x") if span.parent else None,
                "start": datetime.fromtimestamp(span.start_time / 1e9).isoformat(),
                "end": datetime.fromtimestamp(span.end_time / 1e9).isoformat(),
                "duration_ms": round((span.end_time - span.start_time) / 1e6, 2),
                "attributes": dict(span.attributes or {}),
                "status": str(span.status.status_code.name),
            })
        self._flush()
        return SpanExportResult.SUCCESS

    def _flush(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self._spans, f, indent=2, ensure_ascii=False)

    def shutdown(self):
        self._flush()


_initialized = False


def setup_observability(service_name: str = "multiagent-prototype") -> trace.Tracer:
    """Configura OpenTelemetry. Idempotente - pode ser chamado várias vezes."""
    global _initialized
    if not _initialized:
        provider = TracerProvider(
            resource=Resource.create({"service.name": service_name}),
        )
        # Console: visível no terminal durante a execução
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        # JSON file: evidência persistida
        provider.add_span_processor(BatchSpanProcessor(JSONFileSpanExporter(TRACES_FILE)))
        trace.set_tracer_provider(provider)
        _initialized = True
    return trace.get_tracer(service_name)


def get_tracer(name: str = "multiagent") -> trace.Tracer:
    """Obtém um tracer. Garante que a inicialização ocorreu."""
    if not _initialized:
        setup_observability()
    return trace.get_tracer(name)
