import io
from typing import Annotated

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from starlette.status import HTTP_302_FOUND

from chapter_sync import chapter as chapter_actions
from chapter_sync.cli.chapter import Export, Send
from chapter_sync.console import Console
from chapter_sync.email import EmailClient
from chapter_sync.schema import Chapter
from chapter_sync.web.dependencies import console, database, email_client, templates

from kokoro import KPipeline
import soundfile as sf
import torch
import numpy as np
import html2text

def find_chapter(db: Session, series_id: int, chapter_id: int) -> Chapter | None:
    return (
        db.query(Chapter)
        .where(Chapter.series_id == series_id)
        .where(Chapter.id == chapter_id)
        .options(joinedload(Chapter.series))
        .one_or_none()
    )


def get_chapter(
    request: Request,
    db: Annotated[Session, Depends(database)],
    templates: Annotated[Jinja2Templates, Depends(templates)],
    series_id: int,
    chapter_id: int,
):
    chapter = find_chapter(db, series_id, chapter_id)
    return templates.TemplateResponse(
        request=request,
        name="chapter.html",
        context={
            "series": chapter and chapter.series,
            "chapter": chapter,
        },
    )

def export(
    request: Request,
    db: Annotated[Session, Depends(database)],
    console: Annotated[Console, Depends(console)],
    series_id: int,
    chapter_id: int,
):
    chapter = find_chapter(db, series_id, chapter_id)
    assert chapter

    export = Export(series_id, chapter.number, force=True)
    chapter_actions.export(export, db, console)

    return RedirectResponse(
        url=request.url_for(
            "get_chapter",
            series_id=series_id,
            chapter_id=chapter_id,
        ),
        status_code=HTTP_302_FOUND,
    )


def download(
    db: Annotated[Session, Depends(database)],
    series_id: int,
    chapter_id: int,
):
    chapter = find_chapter(db, series_id, chapter_id)

    assert chapter
    assert chapter.ebook
    return StreamingResponse(
        io.BytesIO(chapter.ebook),
        media_type="application/epub+zip",
        headers={"Content-Disposition": f'inline; filename="{chapter.filename()}"'},
    )

def download_audiobook(
    db: Annotated[Session, Depends(database)],
    series_id: int,
    chapter_id: int,
):
    print("Finding Chapter")
    chapter = find_chapter(db, series_id, chapter_id)

    print("Assert Chapter")
    assert chapter
    
    print("Text to TTS")
    h = html2text.HTML2Text()
    h.body_width = 0
    h.single_line_break = True
    text = h.handle(chapter.content)
    print(text)

    print("Create Audio chunk array")
    audio_chunks = []

    print("Creating Pipeline")
    pipeline = KPipeline(lang_code='a')

    print("generating content")
    generator = pipeline(text, voice='af_heart', speed=1, split_pattern=r'\n+')
    
    for i, (gs, ps, audio) in enumerate(generator):
        print(f"Generated chunk {i}...")
        print(gs, ps, sep = "\n", end="\n")
        audio_chunks.append(audio)

    if not audio_chunks:
        print("TTS pipeline did not produce any audio.")
        return {"error": "TTS generation failed to produce audio."}

    full_audio = np.concatenate(audio_chunks)
    print("Audio chunks concatenated.")

    wav_buffer = io.BytesIO()

    sf.write(wav_buffer, full_audio, 24000, format='WAV', subtype='PCM_16')
    print("WAV file created in memory.")

    wav_buffer.seek(0)

    return StreamingResponse(
        wav_buffer,
        media_type="audio/wav",
        headers={"Content-Disposition": f'attachment; filename="{chapter.filename()}.wav"'}
    )


def send(
    request: Request,
    db: Annotated[Session, Depends(database)],
    email_client: Annotated[EmailClient, Depends(email_client)],
    series_id: int,
    chapter_id: int,
):
    chapter = find_chapter(db, series_id, chapter_id)

    assert chapter
    assert chapter.ebook

    send = Send(series_id, chapter.number)
    chapter_actions.send(send, db, email_client)

    return RedirectResponse(
        url=request.url_for(
            "get_chapter",
            series_id=series_id,
            chapter_id=chapter_id,
        ),
        status_code=HTTP_302_FOUND,
    )
