# Browser Native State — APR Runtime v0.4

## Why browser state is a modality

For an agent, information channels include more than human-like senses.

A browser exposes native state:

```text
URL
title
DOM
ARIA/accessibility tree
focus
```

These are often cheaper and more exact than recovering the same facts from
pixels.

## Install

```bash
pip install -e ".[browser]"
playwright install chromium
```

For attaching to an existing Chromium instance, the browser itself must be
started with a remote debugging endpoint that you intentionally expose.

## Run

```bash
python examples/run_browser_native_state.py
```

Default endpoint:

```text
http://127.0.0.1:9222
```

## Security

A CDP endpoint grants powerful browser automation access.

Do not bind it to an untrusted network interface.

Use a dedicated browser/profile for development where possible.

## Fast Loop facts

```text
browser.url
browser.title
browser.aria.digest
browser.dom.digest
browser.dom.element_count
browser.active_element
```

## Goal-time facts

`BrowserStructuredAdapter` additionally exposes:

```text
browser.aria.snapshot
```

so APR can request a deeper native read only when a goal requires it.

## Event types

```text
browser_navigation
browser_aria_changed
browser_dom_changed
browser_focus_changed
```

## Design

```text
native browser state
 -> bounded snapshot
 -> digest
 -> change event
 -> APR policy
```

not:

```text
full screenshot
 -> VLM
 -> rediscover URL/DOM every cycle
```
