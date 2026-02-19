import subprocess
import tempfile
import pathlib

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Csound Controller")

@mcp.tool()
def render_csd(csd_content: str) -> str:
    """
    Render a Csound (.csd) string to a WAV audio file.
    
    Args:
        csd_content: The complete Csound orchestra and score as a string.
        
    Returns:
        The absolute path to the generated .wav file.
    """
    try:
        # Create a temporary file for the .csd input
        with tempfile.NamedTemporaryFile(suffix=".csd", delete=False, mode="w") as csd_file:
            csd_file.write(csd_content)
            csd_path = csd_file.name
            
        # Create a temporary path for the .wav output
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

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
