# Csound MCP Server

The Csound MCP server exposes [Csound](https://csound.com/) audio engine functionality to AI agents via the Model Context Protocol (MCP).

## Features

- **Stateless Architecture:** Lightweight execution using standard Csound.
- **Render to WAV:** Provides a powerful `render_csd` tool that takes a `.csd` string (orchestra + score) and generates a `.wav` file.
- **Tone Synthesis MVP:** Includes a `synthesize_tone` tool that generates a simple monophonic sine wave given a pitch and duration.
- **Subtractive Synthesis:** Includes a `synthesize_subtractive` tool that provides LLM-friendly 0-255 mapped ADSR parameters to shape a sawtooth oscillator run through a lowpass filter.
- **Error Handling:** Gracefully captures and returns `stdout` and `stderr` content to the agent if `csound` compilation or execution fails.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) package manager
- [csound](https://csound.com/download.html) installed and available in the system `$PATH`

## Installation & Running

The package is built with Python and depends on `mcp`. You can run the server directly using `uv`:

```bash
uv run musmcp
```

## Adding to an MCP Client

To configure this server in an MCP client (such as Claude Desktop or Cursor), add it to your configuration (adjust the root path to your workspace directory):

```json
{
  "mcpServers": {
    "musmcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/your/workspace/musmcp",
        "run",
        "musmcp"
      ]
    }
  }
}
```

## Usage Example (Agent perspective)

Once the server is connected, an agent can use the `render_csd` tool to synthesize audio. Here is an example of what an agent would send:

```xml
<CsoundSynthesizer>
<CsOptions>
</CsOptions>
<CsInstruments>
sr = 44100
ksmps = 32
nchnls = 1
0dbfs = 1

instr 1
    a1 poscil 0.5, 440
    out a1
endin
</CsInstruments>
<CsScore>
i 1 0 1
</CsScore>
</CsoundSynthesizer>
```

This will run Csound in the background and return the temporary `.wav` file location for playback.

### Using `synthesize_subtractive`

The `synthesize_subtractive` tool is specifically designed to be easy for LLM agents to use. It abstracts complex Csound envelopes into simple `0-255` integers.

Here is how an agent should map desired sounds to the tool's parameters:

**1. A Plucky/Percussive Bass (Fast attack, fast decay, no sustain)**
```json
{
  "pitch": 55.0,
  "duration": 1.5,
  "cutoff_hz": 400.0,
  "attack": 5,
  "decay": 80,
  "sustain": 0,
  "release": 50
}
```

**2. A Warm Pad (Slow attack, high sustain, long release)**
```json
{
  "pitch": 220.0,
  "duration": 4.0,
  "cutoff_hz": 1200.0,
  "attack": 150,
  "decay": 100,
  "sustain": 200,
  "release": 200
}
```

**3. An Aggressive Lead (Fast attack, high sustain, bright filter)**
```json
{
  "pitch": 880.0,
  "duration": 2.0,
  "cutoff_hz": 4500.0,
  "attack": 10,
  "decay": 50,
  "sustain": 255,
  "release": 20
}
```
