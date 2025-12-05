"""
Test comunicazione stdio MCP - verifica che il protocollo funzioni.
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server


async def main():
    """Test server MCP base con logging dettagliato."""
    
    # Setup logging su stderr (Claude Desktop legge solo stdout per MCP)
    print("[TEST] Inizializzazione server MCP...", file=sys.stderr)
    
    server = Server("edc-lineage-test")
    
    # Contatore chiamate per debug
    call_count = {"list_tools": 0, "call_tool": 0}
    
    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        call_count["list_tools"] += 1
        print(f"[TEST] list_tools chiamato (#{call_count['list_tools']})", file=sys.stderr)
        
        tools = [
            Tool(
                name="ping",
                description="Test di connessione - risponde con pong",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Messaggio opzionale",
                            "default": "ping"
                        }
                    }
                }
            ),
            Tool(
                name="echo",
                description="Ripete il messaggio ricevuto",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Testo da ripetere"
                        }
                    },
                    "required": ["text"]
                }
            )
        ]
        
        print(f"[TEST] Ritorno {len(tools)} tools", file=sys.stderr)
        return tools
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        call_count["call_tool"] += 1
        print(f"[TEST] call_tool '{name}' (#{call_count['call_tool']})", file=sys.stderr)
        print(f"[TEST] Arguments: {arguments}", file=sys.stderr)
        
        try:
            if name == "ping":
                msg = arguments.get("message", "ping")
                response = f"pong! (received: {msg})"
                print(f"[TEST] Risposta ping: {response}", file=sys.stderr)
                return [TextContent(type="text", text=response)]
            
            elif name == "echo":
                text = arguments.get("text", "")
                response = f"Echo: {text}"
                print(f"[TEST] Risposta echo: {response}", file=sys.stderr)
                return [TextContent(type="text", text=response)]
            
            else:
                error_msg = f"Tool sconosciuto: {name}"
                print(f"[TEST] ERRORE: {error_msg}", file=sys.stderr)
                return [TextContent(type="text", text=error_msg)]
                
        except Exception as e:
            error_msg = f"Errore esecuzione tool: {e}"
            print(f"[TEST] ECCEZIONE: {error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]
    
    print("[TEST] Server configurato, avvio stdio_server...", file=sys.stderr)
    print("[TEST] In attesa di connessione da Claude Desktop...", file=sys.stderr)
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            print("[TEST] stdio_server connesso!", file=sys.stderr)
            print("[TEST] Avvio run loop...", file=sys.stderr)
            
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
            
    except Exception as e:
        print(f"[TEST] ERRORE FATALE: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise
    finally:
        print(f"[TEST] Server terminato. Stats: {call_count}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())