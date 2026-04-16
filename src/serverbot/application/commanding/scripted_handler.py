"""Script-driven command handler implementation."""

from __future__ import annotations

import shlex
from dataclasses import dataclass

from serverbot.application.commanding.contracts import CommandHandler
from serverbot.domain.commanding.models import CommandRequest, CommandResponse
from serverbot.domain.commanding.script_models import CommandActionBlock, CommandExceptRule, CommandScript
from serverbot.domain.ports import CommandRunner


@dataclass(frozen=True)
class ScriptedCommandHandler(CommandHandler):
    """Execute scripted command actions from KDL definitions."""

    command_name: str
    runner: CommandRunner
    root_execute: CommandActionBlock
    root_except_rules: tuple[CommandExceptRule, ...]
    subcommands: tuple[tuple[str, CommandScript], ...]

    async def handle(self, request: CommandRequest) -> CommandResponse:
        """Execute command script and render aggregated message."""

        selected_execute = self.root_execute
        selected_except = self.root_except_rules
        args = list(request.raw_tokens)
        subcommand_map = dict(self.subcommands)
        if args and args[0] in subcommand_map:
            selected_script = subcommand_map[args[0]]
            selected_execute = selected_script.execute
            selected_except = selected_script.except_rules
            args = args[1:]
        output, return_code = await self._run_action(selected_execute, args)
        success = return_code == 0
        if not success:
            for rule in selected_except:
                if self._matches(rule.expression, return_code):
                    except_output, _ = await self._run_action(rule.execute, args)
                    output = f"{output}\n{except_output}".strip()
                    break
        return CommandResponse(command_name=self.command_name, message=output.strip(), success=success)

    async def _run_action(self, action: CommandActionBlock, args: list[str]) -> tuple[str, int]:
        """Run one action block and return rendered output and return code."""

        lines: list[str] = []
        status_map: dict[str, str] = {}
        for status_key, message in action.statuses:
            status_map[status_key] = message
        lines.extend(action.prints)
        return_code = 0
        if action.command_template is not None:
            rendered = action.command_template.replace("$@", " ".join(shlex.quote(item) for item in args))
            result = await self.runner.run(["bash", "-lc", rendered])
            return_code = result.return_code
            if action.stream:
                if result.stdout:
                    lines.append(result.stdout.strip())
                if result.stderr:
                    lines.append(result.stderr.strip())
        if status_map:
            lines.extend(status_map.values())
        return "\n".join(line for line in lines if line), return_code

    def _matches(self, expression: str, return_code: int) -> bool:
        """Evaluate return-code condition expression."""

        if expression.isdigit():
            return return_code == int(expression)
        if expression.startswith(">"):
            return return_code > int(expression[1:])
        if expression.startswith("<"):
            return return_code < int(expression[1:])
        return False
