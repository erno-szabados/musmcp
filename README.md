# Csound MCP Server

The Csound MCP server exposes [Csound](https://csound.com/) audio engine functionality to AI agents via the Model Context Protocol (MCP).

## Features

- **Stateless Architecture:** Lightweight execution using standard Csound.
- **Subtractive Synthesis:** Exposes a `synthesize_subtractive` tool that provides LLM-friendly 0-255 mapped ADSR parameters to shape a sawtooth oscillator run through a lowpass filter.
- **Semantic Guardrails:** The tool parameters are heavily documented with acoustic definitions (e.g., matching "fast attack" to integer ranges), and an MCP Resource `lore://sound_design` is provided to teach agents how to synthesize classic instruments.
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

Before using the tool, an agent can read the provided `lore://sound_design` MCP resource to understand how to map acoustic concepts to the `0-255` ADSR integers.

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
  "release": 50,
  "output_filename": "bass_pluck.wav"
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
  "release": 200,
  "output_filename": "warm_pad.wav"
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
  "release": 20,
  "output_filename": "aggr_lead.wav"
}
```
