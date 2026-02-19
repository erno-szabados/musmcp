import subprocess
import tempfile
import pathlib

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Csound Controller")

# Internal helper function, not exposed as a tool
def render_csd(csd_content: str, output_filename: str | None = None) -> str:
    """
    Render a Csound (.csd) string to a WAV audio file.
    
    Args:
        csd_content: The complete Csound orchestra and score as a string.
        output_filename: Optional name for the output file in the current directory.
        
    Returns:
        The absolute path to the generated .wav file.
    """
    try:
        # Create a temporary file for the .csd input
        with tempfile.NamedTemporaryFile(suffix=".csd", delete=False, mode="w") as csd_file:
            csd_file.write(csd_content)
            csd_path = csd_file.name
            
        # Determine the .wav output path
        if output_filename:
            # Ensure it ends with .wav
            if not output_filename.endswith(".wav"):
                output_filename += ".wav"
            wav_path = str(pathlib.Path(output_filename).absolute())
        else:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
                wav_path = wav_file.name

        # Execute csound to render the file
        # -o specifies the output file
        # -W outputs WAV format
        # -d suppresses UI/displays
        cmd = ["csound", "-d", "-W", "-o", wav_path, csd_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Error rendering CSD:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            
        return wav_path

    except Exception as e:
        return f"Failed to execute Csound: {str(e)}"

# Internal helper function, not exposed as a tool
def synthesize_tone(pitch: float, duration: float, output_filename: str | None = None) -> str:
    """
    Generate a simple monophonic sine wave tone.
    
    Args:
        pitch: The frequency of the tone in Hz.
        duration: The duration of the tone in seconds.
        output_filename: Optional name for the output file.
        
    Returns:
        The absolute path to the generated .wav file.
    """
    csd_template = f"""<CsoundSynthesizer>
<CsOptions>
</CsOptions>
<CsInstruments>
sr = 44100
ksmps = 32
nchnls = 1
0dbfs = 1

instr 1
    a1 poscil 0.5, {pitch}
    out a1
endin
</CsInstruments>
<CsScore>
i 1 0 {duration}
</CsScore>
</CsoundSynthesizer>"""
    return render_csd(csd_template, output_filename)

def map_0_255_to_range(val: int, min_val: float, max_val: float) -> float:
    """Map an integer 0-255 linearly to a float range."""
    return min_val + (max_val - min_val) * (val / 255.0)

@mcp.tool()
def synthesize_subtractive(
    pitch: float, 
    duration: float, 
    cutoff_hz: float, 
    attack: int, 
    decay: int, 
    sustain: int, 
    release: int,
    output_filename: str | None = None
) -> str:
    """
    Generate a tone using subtractive synthesis (sawtooth + lowpass filter).
    
    Args:
        pitch: The fundamental frequency in Hz (e.g., 55.0 for Bass, 440.0 for Lead).
        duration: The total length of the note in seconds.
        cutoff_hz: Filter brightness. 
            - 100-400: Dark, muffled (Bass, Deep Pads)
            - 800-1500: Warm, midrange (Warm Pads, Keys)
            - 2000-5000: Bright, piercing (Leads, Plucks)
        attack: Time to reach max volume (0-255).
            - 0-10: Instant hit (Plucks, Kicks, Percussive Bass)
            - 50-100: Medium swell (Soft Leads, Strings)
            - 150-255: Very slow fade in (Ambient Pads, Drones)
        decay: Time to drop from max volume to sustain level (0-255).
            - 10-50: Fast drop (Punchy Bass)
            - 80-150: Natural decay (Keys, Guitars)
        sustain: Level held after decay phase (0-255).
            - 0: Note dies out entirely (Plucks, Percussion)
            - 255: Note holds at maximum volume (Organs, Synths)
        release: Fade out time after the note ends (0-255).
            - 10-30: Stops immediately (Staccato Bass, Tight Leads)
            - 150-255: Long ringing tail (Cinematic Pads, Reverbs)
        output_filename: Optional name for the output file (e.g. 'warm_pad.wav').
        
    Returns:
        The absolute path to making the generated .wav file.
    """
    # Clamp inputs just in case
    att = max(0, min(255, attack))
    dec = max(0, min(255, decay))
    sus = max(0, min(255, sustain))
    rel = max(0, min(255, release))
    
    # Map to real seconds/levels
    att_sec = map_0_255_to_range(att, 0.001, 2.0)
    dec_sec = map_0_255_to_range(dec, 0.001, 2.0)
    sus_lvl = map_0_255_to_range(sus, 0.0, 1.0)
    rel_sec = map_0_255_to_range(rel, 0.001, 5.0)
    
    # We must add release time to overall score duration so the tail isn't cut off
    score_duration = duration + rel_sec
    
    csd = f"""<CsoundSynthesizer>
<CsOptions>
</CsOptions>
<CsInstruments>
sr = 44100
ksmps = 32
nchnls = 1
0dbfs = 1

instr 1
    ; 1. Amplitude ADSR 
    ; madsr allows the note to release over time when it finishes
    kamp madsr {att_sec}, {dec_sec}, {sus_lvl}, {rel_sec}
    
    ; 2. Oscillator - Sawtooth (vco2 mode 0 is saw)
    asig vco2 1.0, {pitch}, 0
    
    ; 3. Filter - Moog ladder lowpass
    ; We add a slight envelope to the filter cutoff for more dynamic sound
    kfilt_env expseg {cutoff_hz}*3, {att_sec}+{dec_sec}, {cutoff_hz}
    afil moogladder asig, kfilt_env, 0.4
    
    ; 4. Output (reduced master amplitude by 0.5 to leave headroom)
    out (afil * kamp) * 0.5
endin
</CsInstruments>
<CsScore>
; Play instr 1, from start=0, for specified parameter duration.
; The madsr opcode handles extending the note for the release phase.
i 1 0 {duration}
</CsScore>
</CsoundSynthesizer>"""
    return render_csd(csd, output_filename)

@mcp.resource("lore://sound_design")
def get_sound_design_lore() -> str:
    """Cheat sheet for configuring standard synth archetypes with synthesize_subtractive."""
    return """
SOUND DESIGN CHEATSHEET for Subtractive Synthesis Tool

1. BASS PLUCK / PERCUSSION
Description: Short, punchy, dark, dies away quickly.
Parameters:
- pitch: Low (30Hz - 80Hz)
- cutoff_hz: Low to Medium (200 - 800)
- attack: Very Low (0-10)
- decay: Medium Low (50-100)
- sustain: Zero (0) - It should not hold!
- release: Medium Low (30-80)

2. WARM PAD / AMBIENCE
Description: Slow building, warm, sustains forever, long fade out.
Parameters:
- pitch: Mid (150Hz - 400Hz)
- cutoff_hz: Medium (800 - 1500)
- attack: High (150-255)
- decay: Medium (100)
- sustain: High (150-255)
- release: High (150-255)

3. AGGRESSIVE LEAD
Description: Bright, fast attacking, holds steady for melodies.
Parameters:
- pitch: High (400Hz - 1000Hz)
- cutoff_hz: High (3000 - 5000)
- attack: Low (0-20)
- decay: Low (50)
- sustain: Max (255)
- release: Low (20-50)
"""

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
