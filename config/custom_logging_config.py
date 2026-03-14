from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
import logging
import json
from typing import Any


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


class RequestLoggingMiddleware(Middleware):
    """Log all incoming requests and outgoing responses with timing information."""
    
    def _format_data(self, data: Any, indent: int = 0) -> str:
        """Format data for pretty printing."""
        try:
            if isinstance(data, (dict, list)):
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                lines = json_str.split('\n')
                if len(lines) > 10:
                    return '\n'.join(lines[:10]) + f'\n{Colors.DIM}... ({len(lines) - 10} more lines){Colors.RESET}'
                return json_str
            return str(data)
        except:
            return str(data)
    
    def _log_separator(self, char: str = "─", length: int = 80, color: str = Colors.BRIGHT_BLACK):
        """Log a visual separator line."""
        logging.info(f"{color}{char * length}{Colors.RESET}")
    
    def _log_header(self, emoji: str, title: str, color: str = Colors.BRIGHT_CYAN):
        """Log a formatted header."""
        logging.info(f"{color}{Colors.BOLD}{emoji} {title}{Colors.RESET}")
        self._log_separator("═", 80, color)
    
    def _extract_tools_from_result(self, result: Any) -> list:
        """Extract tool names and descriptions from tools/list result."""
        tools = []
        if isinstance(result, dict) and 'tools' in result:
            for tool in result['tools']:
                if isinstance(tool, dict):
                    name = tool.get('name', 'unknown')
                    desc = tool.get('description', '')
                    tools.append(f"{name}: {desc}")
        elif isinstance(result, list):
            for tool in result:
                if hasattr(tool, 'name'):
                    name = tool.name
                    desc = getattr(tool, 'description', '')
                    tools.append(f"{name}: {desc}")
                elif isinstance(tool, dict):
                    name = tool.get('name', 'unknown')
                    desc = tool.get('description', '')
                    tools.append(f"{name}: {desc}")
        return tools
    
    def _extract_tool_call_info(self, message: Any) -> tuple[str, dict]:
        """Extract tool name and arguments from tools/call message."""
        if hasattr(message, 'name') and hasattr(message, 'arguments'):
            return message.name, message.arguments
        elif isinstance(message, dict):
            return message.get('name', 'unknown'), message.get('arguments', {})
        return 'unknown', {}
    
    def _extract_tool_result(self, result: Any) -> Any:
        """Extract the actual result from tool call response."""
        if hasattr(result, 'content'):
            if isinstance(result.content, list) and len(result.content) > 0:
                first_item = result.content[0]
                if hasattr(first_item, 'text'):
                    return first_item.text
            return result.content
        elif isinstance(result, dict):
            if 'content' in result:
                content = result['content']
                if isinstance(content, list) and len(content) > 0:
                    first_item = content[0]
                    if isinstance(first_item, dict) and 'text' in first_item:
                        return first_item['text']
                return content
            if 'result' in result:
                return result['result']
        return result
    
    async def on_message(self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]) -> Any:
        method = context.method
        
        try:
            result = await call_next(context)
            
            # Special handling for tools/list
            if method == "tools/list":
                logging.info(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}📋 TOOLS LIST{Colors.RESET}")
                self._log_separator("═", 80, Colors.BRIGHT_CYAN)
                tools = self._extract_tools_from_result(result)
                for i, tool in enumerate(tools, 1):
                    logging.info(f"{Colors.CYAN}{i}.{Colors.RESET} {Colors.BRIGHT_WHITE}{tool}{Colors.RESET}")
                self._log_separator("═", 80, Colors.BRIGHT_CYAN)
                logging.info("")
            
            # Special handling for tools/call
            elif method == "tools/call":
                tool_name, arguments = self._extract_tool_call_info(context.message)
                tool_result = self._extract_tool_result(result)
                
                logging.info(f"{Colors.BRIGHT_GREEN}{Colors.BOLD}🔧 TOOL CALL{Colors.RESET}")
                self._log_separator("═", 80, Colors.BRIGHT_GREEN)
                logging.info(f"{Colors.BOLD}Tool:{Colors.RESET} {Colors.BRIGHT_YELLOW}{tool_name}{Colors.RESET}")
                
                logging.info(f"{Colors.CYAN}┌─ Arguments{Colors.RESET}")
                formatted_args = self._format_data(arguments)
                for line in formatted_args.split('\n'):
                    logging.info(f"{Colors.CYAN}│{Colors.RESET} {line}")
                logging.info(f"{Colors.CYAN}──────────────────────{Colors.RESET}")
                
                logging.info(f"{Colors.MAGENTA}┌─ Response{Colors.RESET}")
                formatted_result = self._format_data(tool_result)
                for line in formatted_result.split('\n'):
                    logging.info(f"{Colors.MAGENTA}│{Colors.RESET} {line}")
                logging.info(f"{Colors.MAGENTA}──────────────────────{Colors.RESET}")
                
                self._log_separator("═", 80, Colors.BRIGHT_GREEN)
                logging.info("")
            
            # Generic handling for other methods
            else:
                self._log_header("📥", f"REQUEST: {method}", Colors.BRIGHT_BLUE)
                
                if context.message:
                    logging.info(f"{Colors.MAGENTA}┌─ Payload{Colors.RESET}")
                    formatted_message = self._format_data(context.message)
                    for line in formatted_message.split('\n'):
                        logging.info(f"{Colors.MAGENTA}│{Colors.RESET} {line}")
                    logging.info(f"{Colors.MAGENTA}──────────────────────{Colors.RESET}")
                
                self._log_header("📤", f"RESPONSE: {method}", Colors.BRIGHT_GREEN)
                
                if result is not None:
                    logging.info(f"{Colors.BRIGHT_MAGENTA}┌─ Result{Colors.RESET}")
                    formatted_result = self._format_data(result)
                    for line in formatted_result.split('\n'):
                        logging.info(f"{Colors.BRIGHT_MAGENTA}│{Colors.RESET} {line}")
                    logging.info(f"{Colors.BRIGHT_MAGENTA}──────────────────────{Colors.RESET}")
                
                logging.info(f"{Colors.BRIGHT_GREEN}✅ SUCCESS{Colors.RESET}")
                self._log_separator("═", 80, Colors.BRIGHT_GREEN)
                logging.info("")
            
            return result
            
        except Exception as e:
            self._log_header("📤", f"ERROR: {method}", Colors.BRIGHT_RED)
            
            logging.info(f"{Colors.BRIGHT_RED}┌─ Error Details{Colors.RESET}")
            error_lines = str(e).split('\n')
            for line in error_lines:
                logging.info(f"{Colors.BRIGHT_RED}│{Colors.RESET} {Colors.RED}{line}{Colors.RESET}")
            logging.info(f"{Colors.BRIGHT_RED}└─{Colors.RESET}")
            
            logging.info(f"{Colors.BRIGHT_RED}{Colors.BOLD}❌ REQUEST FAILED{Colors.RESET}")
            self._log_separator("═", 80, Colors.BRIGHT_RED)
            logging.info("")
            
            raise
