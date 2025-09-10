---
trigger: manual
---

# Development Assistant Rules

## Environment Management (Rules 1-4)
1. **Always check for virtual environments first** - Look for `.venv`, `venv`, or similar directories before running Python commands
2. **Use virtual environment paths explicitly** - When venv exists, use `.venv\Scripts\python.exe` or `.venv\Scripts\pip.exe` instead of global commands
3. **Verify package installation location** - Check if packages are being installed globally vs. in venv using `pip show` or `pip list`
4. **Update requirements.txt proactively** - When installing new packages, immediately add them to requirements.txt with appropriate version constraints

## Server and Process Management (Rules 5-8)
5. **Check for running processes before starting servers** - Use `Get-Process` or similar to avoid port conflicts
6. **Use appropriate ports** - Check the application code for configured ports (e.g., FastAPI on 8010, Flask on 5001)
7. **Stop processes cleanly** - Use proper shutdown commands before starting new instances
8. **Monitor background processes** - Use command_status to track long-running commands

## Code Analysis and Modification (Rules 9-12)
9. **Read before editing** - Always examine existing code structure before making changes
10. **Preserve existing patterns** - Match the coding style, import patterns, and architecture already in use
11. **Check dependencies** - Verify all required imports and packages are available before running code
12. **Test changes incrementally** - Make small changes and verify they work before proceeding

## File and Directory Operations (Rules 13-16)
13. **Use absolute paths** - Always provide full paths to avoid ambiguity
14. **Check file existence** - Verify files exist before attempting to read or modify them
15. **Respect project structure** - Don't create files in inappropriate locations (e.g., avoid .windsurf directories)
16. **Backup important changes** - Consider the impact of modifications on existing functionality

## Communication and Planning (Rules 17-20)
17. **Use todo_list for complex tasks** - Break down multi-step processes and track progress
18. **Update todos immediately** - Mark items complete as soon as they're finished
19. **Be specific about errors** - Provide exact error messages and file paths when issues occur
20. **Explain technical decisions** - Clarify why certain approaches are chosen over alternatives

## Browser and UI Management (Rules 21-23)
21. **Match server configuration** - Ensure browser previews point to the correct host and port
22. **Verify server startup** - Check that servers are actually running before creating previews
23. **Handle static file serving** - Ensure CSS, JS, and other assets are properly configured

## Memory and Context Management (Rules 24-26)
24. **Save important context** - Create memories for significant discoveries, user preferences, and project-specific information
25. **Reference previous solutions** - Check for similar issues that have been resolved before
26. **Document environment quirks** - Note any unusual project setup or configuration requirements

## Error Handling and Recovery (Rules 27-30)
27. **Provide alternative approaches** - If one method fails, suggest different ways to achieve the same goal
28. **Clean up failed attempts** - Remove or fix incomplete installations or configurations
29. **Verify solutions work** - Test that fixes actually resolve the reported issues
30. **Learn from failures** - Update approach based on what doesn't work in the specific environment

## Windows-Specific Considerations
31. **Use Windows-compatible commands** - Prefer PowerShell syntax over bash when on Windows
32. **Handle path separators correctly** - Use backslashes for Windows paths in commands
33. **Account for execution policies** - Be aware of PowerShell script execution restrictions
34. **Use appropriate file extensions** - Recognize .bat, .ps1, and .exe files for Windows environments
