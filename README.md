# whatsapp-cloud-api-py

Community-built async Python SDK for the WhatsApp Business Cloud API.

> **Note:** This is an **independent Python implementation** — not a port or fork. It was inspired by the excellent [`@kapso/whatsapp-cloud-api`](https://github.com/gokapso/whatsapp-cloud-api-js) (TypeScript), but written from scratch in Python with its own architecture, design choices, and API surface.

Built with **httpx** (HTTP/2 + connection pooling), **Pydantic V2** (Rust-powered validation), and optional **pyventus** event-driven webhooks.

## Features

- **Fully async** — all I/O uses `async`/`await` with httpx
- **HTTP/2** — connection pooling and multiplexing out of the box
- **Pydantic V2** — fast, type-safe input/response models with Rust-powered validation
- **27 message types** — text, image, video, audio, document, sticker, location, contacts, reaction, template, interactive (buttons, list, flow, CTA URL, catalog), mark as read
- **Media operations** — upload, get metadata, download, delete (with auto-retry on auth failures)
- **Template management** — list, create, delete message templates
- **Phone number management** — registration, verification, business profile
- **WhatsApp Flows** — create and deploy (auto-publish)
- **Webhook handling** — HMAC-SHA256 signature verification + payload normalization
- **Event-driven webhooks** — optional pyventus integration with 18 typed events
- **Error categorization** — 14 error categories with retry hints (but no forced auto-retry)

## Installation

```bash
uv add whatsapp-cloud-api-py
```

With extras:

```bash
# Event-driven webhooks (pyventus)
uv add "whatsapp-cloud-api-py[events]"

# All extras
uv add "whatsapp-cloud-api-py[events,webhooks,server]"
```

## Quick Start

```python
import asyncio
from whatsapp_cloud_api import WhatsAppClient, TextMessage

async def main():
    async with WhatsAppClient(access_token="YOUR_TOKEN") as client:
        response = await client.messages.send_text(TextMessage(
            phone_number_id="PHONE_NUMBER_ID",
            to="5511999999999",
            body="Hello from Python!",
        ))
        print(response.messages[0].id)

asyncio.run(main())
```

## Sending Messages

All message types return a `SendMessageResponse` with `contacts` and `messages` fields.

### Text

```python
from whatsapp_cloud_api import TextMessage

await client.messages.send_text(TextMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    body="Hello!",
    preview_url=True,  # enable link previews
))
```

### Image

```python
from whatsapp_cloud_api import ImageMessage
from whatsapp_cloud_api.resources.messages import MediaById, MediaByLink

# By media ID (from upload)
await client.messages.send_image(ImageMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    image=MediaById(id="MEDIA_ID", caption="Check this out"),
))

# By URL
await client.messages.send_image(ImageMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    image=MediaByLink(link="https://example.com/photo.jpg"),
))
```

### Audio / Video / Document / Sticker

```python
from whatsapp_cloud_api import AudioMessage, VideoMessage, DocumentMessage, StickerMessage
from whatsapp_cloud_api.resources.messages import (
    AudioPayloadByLink, MediaByLink, DocumentPayloadByLink, StickerByLink,
)

await client.messages.send_audio(AudioMessage(
    phone_number_id="PHONE_ID", to="5511999999999",
    audio=AudioPayloadByLink(link="https://example.com/audio.mp3"),
))

await client.messages.send_video(VideoMessage(
    phone_number_id="PHONE_ID", to="5511999999999",
    video=MediaByLink(link="https://example.com/video.mp4", caption="Watch this"),
))

await client.messages.send_document(DocumentMessage(
    phone_number_id="PHONE_ID", to="5511999999999",
    document=DocumentPayloadByLink(
        link="https://example.com/file.pdf",
        filename="report.pdf",
        caption="Monthly report",
    ),
))

await client.messages.send_sticker(StickerMessage(
    phone_number_id="PHONE_ID", to="5511999999999",
    sticker=StickerByLink(link="https://example.com/sticker.webp"),
))
```

### Location

```python
from whatsapp_cloud_api import LocationMessage
from whatsapp_cloud_api.resources.messages import LocationPayload

await client.messages.send_location(LocationMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    location=LocationPayload(
        latitude=-23.5505,
        longitude=-46.6333,
        name="Sao Paulo",
        address="Av. Paulista, 1000",
    ),
))
```

### Contacts

```python
from whatsapp_cloud_api import ContactsMessage
from whatsapp_cloud_api.resources.messages import Contact, ContactName, ContactPhone

await client.messages.send_contacts(ContactsMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    contacts=[Contact(
        name=ContactName(formatted_name="Maria Silva", first_name="Maria"),
        phones=[ContactPhone(phone="+5511988887777", type="MOBILE")],
    )],
))
```

### Reaction

```python
from whatsapp_cloud_api import ReactionMessage
from whatsapp_cloud_api.resources.messages import ReactionPayload

await client.messages.send_reaction(ReactionMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    reaction=ReactionPayload(message_id="wamid.xxx", emoji="👍"),
))
```

### Template

```python
from whatsapp_cloud_api import TemplateMessage
from whatsapp_cloud_api.resources.messages import TemplatePayload, TemplateLanguage

await client.messages.send_template(TemplateMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    template=TemplatePayload(
        name="hello_world",
        language=TemplateLanguage(code="en_US"),
    ),
))
```

### Interactive Buttons

```python
from whatsapp_cloud_api import InteractiveButtonsMessage
from whatsapp_cloud_api.resources.messages import InteractiveButton

await client.messages.send_interactive_buttons(InteractiveButtonsMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    body_text="Choose an option:",
    buttons=[
        InteractiveButton(id="opt_1", title="Option 1"),
        InteractiveButton(id="opt_2", title="Option 2"),
        InteractiveButton(id="opt_3", title="Option 3"),
    ],
))
```

### Interactive List

```python
from whatsapp_cloud_api import InteractiveListMessage
from whatsapp_cloud_api.resources.messages import ListSection, ListRow

await client.messages.send_interactive_list(InteractiveListMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    body_text="Pick a product:",
    button_text="View options",
    sections=[ListSection(
        title="Products",
        rows=[
            ListRow(id="p1", title="Product A", description="$10.00"),
            ListRow(id="p2", title="Product B", description="$20.00"),
        ],
    )],
))
```

### Interactive Flow

```python
from whatsapp_cloud_api import InteractiveFlowMessage
from whatsapp_cloud_api.resources.messages import FlowParameters

await client.messages.send_interactive_flow(InteractiveFlowMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    body_text="Complete the form:",
    parameters=FlowParameters(
        flow_id="FLOW_ID",
        flow_cta="Open Form",
        flow_action="navigate",
    ),
))
```

### Interactive CTA URL

```python
from whatsapp_cloud_api import InteractiveCtaUrlMessage
from whatsapp_cloud_api.resources.messages import CtaUrlParameters

await client.messages.send_interactive_cta_url(InteractiveCtaUrlMessage(
    phone_number_id="PHONE_ID",
    to="5511999999999",
    body_text="Visit our website",
    parameters=CtaUrlParameters(display_text="Open", url="https://example.com"),
))
```

### Mark as Read

```python
from whatsapp_cloud_api import MarkReadInput

await client.messages.mark_read(MarkReadInput(
    phone_number_id="PHONE_ID",
    message_id="wamid.xxx",
))
```

## Media

```python
from whatsapp_cloud_api.resources.media import MediaUploadInput

# Upload
result = await client.media.upload(MediaUploadInput(
    phone_number_id="PHONE_ID",
    type="image",
    file=open("photo.jpg", "rb").read(),
    filename="photo.jpg",
    mime_type="image/jpeg",
))
print(result.id)  # media ID to use in messages

# Get metadata
meta = await client.media.get("MEDIA_ID")
print(meta.url, meta.mime_type)

# Download
data = await client.media.download("MEDIA_ID")

# Delete
await client.media.delete("MEDIA_ID")
```

## Templates

```python
from whatsapp_cloud_api.resources.templates import (
    TemplateListInput, TemplateCreateInput, TemplateDeleteInput,
)

# List
templates = await client.templates.list(TemplateListInput(
    business_account_id="WABA_ID",
))

# Create
result = await client.templates.create(TemplateCreateInput(
    business_account_id="WABA_ID",
    name="order_confirmation",
    language="pt_BR",
    category="UTILITY",
    components=[
        {"type": "BODY", "text": "Pedido {{1}} confirmado!"},
    ],
))

# Delete
await client.templates.delete(TemplateDeleteInput(
    business_account_id="WABA_ID",
    name="order_confirmation",
))
```

## Phone Numbers

```python
from whatsapp_cloud_api.resources.phone_numbers import (
    RequestCodeInput, VerifyCodeInput, RegisterInput, UpdateBusinessProfileInput,
)

# Request verification code
await client.phone_numbers.request_code(RequestCodeInput(
    phone_number_id="PHONE_ID", code_method="SMS", language="pt_BR",
))

# Verify
await client.phone_numbers.verify_code(VerifyCodeInput(
    phone_number_id="PHONE_ID", code="123456",
))

# Register
await client.phone_numbers.register(RegisterInput(
    phone_number_id="PHONE_ID", pin="123456",
))

# Business profile
profile = await client.phone_numbers.business_profile.get("PHONE_ID")

await client.phone_numbers.business_profile.update(UpdateBusinessProfileInput(
    phone_number_id="PHONE_ID",
    about="We sell things",
    description="Best store in town",
    websites=["https://example.com"],
))
```

## Webhooks

### Signature Verification

```python
from whatsapp_cloud_api import verify_signature

is_valid = verify_signature(
    app_secret="YOUR_META_APP_SECRET",
    raw_body=request_body_bytes,
    signature_header=request.headers.get("x-hub-signature-256"),
)
```

### Payload Normalization

```python
from whatsapp_cloud_api import normalize_webhook

webhook = normalize_webhook(payload)

print(webhook.phone_number_id)
print(webhook.messages)   # list[WebhookMessage]
print(webhook.statuses)   # list[MessageStatusUpdate]
print(webhook.contacts)   # list[dict]
```

## Event-Driven Webhooks (pyventus)

Install with `uv add "whatsapp-cloud-api-py[events]"`.

Instead of manually parsing webhook payloads with `if/elif` chains, use typed event handlers:

```python
from whatsapp_cloud_api import normalize_webhook, verify_signature
from whatsapp_cloud_api.events import (
    dispatch_webhook,
    TextReceived,
    ImageReceived,
    ButtonReply,
    ListReply,
    FlowResponse,
    LocationReceived,
    ReactionReceived,
    OrderReceived,
    MessageDelivered,
    MessageRead,
    MessageFailed,
)
from pyventus.events import EventLinker, AsyncIOEventEmitter


@EventLinker.on(TextReceived)
async def handle_text(event: TextReceived):
    print(f"Text from {event.from_number}: {event.body}")


@EventLinker.on(ImageReceived)
async def handle_image(event: ImageReceived):
    media_bytes = await client.media.download(event.image_id)
    # process image...


@EventLinker.on(ButtonReply)
async def handle_button(event: ButtonReply):
    print(f"Button pressed: {event.button_id} ({event.button_title})")


@EventLinker.on(MessageFailed)
async def handle_failure(event: MessageFailed):
    logger.error(f"Message {event.message_id} failed: {event.errors}")


# Dispatch
webhook = normalize_webhook(raw_payload)
emitter = AsyncIOEventEmitter()
dispatch_webhook(webhook, emitter)
```

### FastAPI Integration

```python
from fastapi import FastAPI, Request, Depends, HTTPException
from pyventus.events import EventLinker, FastAPIEventEmitter
from whatsapp_cloud_api import WhatsAppClient, normalize_webhook, verify_signature
from whatsapp_cloud_api.events import dispatch_webhook, TextReceived

app = FastAPI()
client = WhatsAppClient(access_token="YOUR_TOKEN")
APP_SECRET = "YOUR_META_APP_SECRET"


@EventLinker.on(TextReceived)
async def echo(event: TextReceived):
    from whatsapp_cloud_api import TextMessage
    await client.messages.send_text(TextMessage(
        phone_number_id=event.phone_number_id,
        to=event.from_number,
        body=f"You said: {event.body}",
    ))


@app.post("/webhook")
async def webhook(request: Request, emitter=Depends(FastAPIEventEmitter())):
    body = await request.body()
    if not verify_signature(
        app_secret=APP_SECRET,
        raw_body=body,
        signature_header=request.headers.get("x-hub-signature-256"),
    ):
        raise HTTPException(status_code=403)

    data = normalize_webhook(await request.json())
    dispatch_webhook(data, emitter)
    return {"status": "ok"}


@app.get("/webhook")
async def verify_webhook(mode: str = "", token: str = "", challenge: str = ""):
    if mode == "subscribe" and token == "YOUR_VERIFY_TOKEN":
        return int(challenge)
    raise HTTPException(status_code=403)
```

The `FastAPIEventEmitter` runs handlers via Starlette's `BackgroundTasks`, so the endpoint returns immediately while events are processed in the background.

### Available Events

| Event | Trigger | Key Fields |
|---|---|---|
| `TextReceived` | Text message | `body`, `from_number` |
| `ImageReceived` | Image message | `image_id`, `mime_type`, `caption` |
| `VideoReceived` | Video message | `video_id`, `mime_type`, `caption` |
| `AudioReceived` | Audio/voice note | `audio_id`, `mime_type`, `voice` |
| `DocumentReceived` | Document | `document_id`, `filename`, `caption` |
| `StickerReceived` | Sticker | `sticker_id`, `animated` |
| `LocationReceived` | Location | `latitude`, `longitude`, `name` |
| `ContactsReceived` | Contact card(s) | `contacts` |
| `ReactionReceived` | Reaction emoji | `emoji`, `reacted_message_id` |
| `ButtonReply` | Interactive button | `button_id`, `button_title` |
| `ListReply` | Interactive list | `list_id`, `list_title` |
| `FlowResponse` | WhatsApp Flow | `response_json`, `flow_token` |
| `OrderReceived` | Product order | `catalog_id`, `product_items` |
| `MessageSent` | Status: sent | `message_id`, `recipient_id` |
| `MessageDelivered` | Status: delivered | `message_id`, `recipient_id` |
| `MessageRead` | Status: read | `message_id`, `recipient_id` |
| `MessageFailed` | Status: failed | `message_id`, `errors` |
| `UnknownMessageReceived` | Unmapped type | `raw_type`, `raw_data` |

All events inherit from `WhatsAppEvent` and include `phone_number_id`. Message events also include `message_id`, `timestamp`, `from_number`, and `context`.

## Error Handling

```python
from whatsapp_cloud_api import GraphApiError

try:
    await client.messages.send_text(msg)
except GraphApiError as e:
    print(e.category)       # "throttling", "authorization", "parameter", ...
    print(e.retry.action)   # "retry", "retry_after", "fix_and_retry", "do_not_retry", "refresh_token"
    print(e.retry.retry_after_ms)  # milliseconds to wait (for rate limits)

    if e.is_rate_limit():
        await asyncio.sleep(e.retry.retry_after_ms / 1000)
        # retry...

    if e.requires_token_refresh():
        # refresh your access token
        pass
```

## Client Configuration

```python
from whatsapp_cloud_api import WhatsAppClient

# Default: graph.facebook.com, v23.0, HTTP/2, 30s timeout
client = WhatsAppClient(access_token="TOKEN")

# Custom configuration
client = WhatsAppClient(
    access_token="TOKEN",
    base_url="https://graph.facebook.com",
    graph_version="v23.0",
    timeout=60.0,
)

# Bring your own httpx client
import httpx
custom_http = httpx.AsyncClient(http2=True, timeout=60.0)
client = WhatsAppClient(access_token="TOKEN", http_client=custom_http)

# Always use as async context manager
async with WhatsAppClient(access_token="TOKEN") as client:
    await client.messages.send_text(...)
```

## Project Structure

```
src/whatsapp_cloud_api/
    __init__.py                         # Public API
    client.py                           # Async HTTP client (httpx, HTTP/2)
    types.py                            # Pydantic response models
    errors/
        graph_api_error.py              # GraphApiError + from_response()
        categorize.py                   # Error code -> category mapping
        retry.py                        # RetryHint (action + delay)
    resources/
        messages/
            models.py                   # Pydantic models for all message types
            resource.py                 # MessagesResource (20+ send methods)
        templates/
            models.py                   # Template CRUD input models
            resource.py                 # TemplatesResource
        media.py                        # Upload, download, get, delete
        phone_numbers.py                # Registration, verification, profile
        flows.py                        # Flow management + deploy
    webhooks/
        verify.py                       # HMAC-SHA256 signature verification
        normalize.py                    # Webhook payload normalization
    events/
        events.py                       # Dataclass events (18 types)
        dispatcher.py                   # NormalizedWebhook -> pyventus events
    utils/
        case.py                         # snake_case <-> camelCase (cached)
```

## Acknowledgments

This project was inspired by [`@kapso/whatsapp-cloud-api`](https://github.com/gokapso/whatsapp-cloud-api-js), a TypeScript client for the same API. While the two projects cover similar ground, this Python SDK was written independently with its own architecture and design decisions.

## License

MIT
