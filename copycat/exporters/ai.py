"""AI project summary via OpenAI-compatible API."""

import logging
from pathlib import Path


def _generate_ai_summary(files: dict, input_dir, git_info: str, stats=None,
                          model: str = "gpt-4o-mini", base_url: str = None) -> str:
    """Generate an AI project summary using an OpenAI-compatible API.

    The API key is read exclusively from the ``COPYCAT_AI_KEY`` environment variable.
    Raises ImportError when openai is not installed.
    Raises ValueError on missing API key or API errors.

    Note: Only project metadata (file names, counts) is sent to the API – never
    source code content. Use ``base_url`` for a local Ollama instance.
    """
    import os
    api_key = os.environ.get("COPYCAT_AI_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "Umgebungsvariable COPYCAT_AI_KEY nicht gesetzt.\n"
            "  OpenAI:  set COPYCAT_AI_KEY=sk-...\n"
            "  Ollama:  set COPYCAT_AI_KEY=ollama  (und --ai-base-url http://localhost:11434/v1)"
        )
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "openai-Bibliothek nicht installiert. Bitte: pip install openai"
        ) from exc

    # Build compact project description (no source code sent to external API)
    total = sum(len(v) for v in files.values())
    desc_lines = [
        f"Projektname: {Path(input_dir).name}",
        f"Pfad: {input_dir}",
        f"Git: {git_info}",
        f"Dateien gesamt: {total}",
    ]
    for t, flist in files.items():
        if flist:
            desc_lines.append(f"  {t.upper()}: {len(flist)} Datei(en)")
    if stats:
        tot = stats["total"]
        desc_lines.append(
            f"Codezeilen: {tot['loc']} (Code: {tot['code']}, "
            f"Kommentaranteil: {tot['comment_ratio']}%)"
        )
    code_sample = [f.name for f in files.get("code", [])[:25]]
    if code_sample:
        desc_lines.append("Code-Dateien (Auswahl): " + ", ".join(code_sample))

    prompt = (
        "Analysiere diese CopyCat-Projektbeschreibung und erstelle einen kompakten "
        "Projektsteckbrief auf Deutsch (max. 200 W\u00f6rter). Erkl\u00e4re kurz: Projektzweck, "
        "Technologie-Stack, Struktur und m\u00f6gliche Qualit\u00e4tshinweise.\n\n"
        "Projektbeschreibung:\n" + "\n".join(desc_lines)
    )

    client_kwargs: dict = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    client = OpenAI(**client_kwargs)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        raise ValueError(f"AI-API-Fehler: {exc}") from exc
