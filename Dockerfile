# CopyCat Docker Image
# Build:  docker build -t copycat .
# Run:    docker run --rm -v "$(pwd):/project" copycat --recursive --format html
#
# Alle Kernoptionen funktionieren im Container.
# Der gescannte Ordner wird per Volume-Mount eingebunden:
#   docker run --rm -v "/pfad/zum/projekt:/project" copycat [OPTIONEN]
# Der Report erscheint im gemounteten Ordner.

FROM python:3.12-slim

LABEL org.opencontainers.image.title="CopyCat" \
      org.opencontainers.image.description="Automatischer Projekt-Dokumentierer" \
      org.opencontainers.image.version="2.9"

# Abhängigkeiten installieren (alle optionalen inklusive)
RUN pip install --no-cache-dir \
    reportlab \
    jinja2 \
    watchdog \
    pygments \
    openai

WORKDIR /app

COPY CopyCat.py .
COPY plugins/ ./plugins/

# Standard-Eingabeordner: /project (per Volume-Mount)
VOLUME ["/project"]

ENTRYPOINT ["python", "/app/CopyCat.py", "--input", "/project", "--output", "/project"]
CMD []
