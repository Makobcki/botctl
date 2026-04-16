"""Loader for command creation KDL files under commands/."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from serverbot.domain.commanding.models import CommandDescriptor
from serverbot.domain.commanding.script_models import (
    CommandActionBlock,
    CommandDefinition,
    CommandExceptRule,
    CommandScript,
)
from serverbot.domain.errors import DomainError


@dataclass(frozen=True)
class CommandKdlLoader:
    """Parse command definitions from a constrained KDL dialect."""

    def load(self, path: str) -> tuple[CommandDescriptor, ...]:
        """Load only descriptors for help and routing."""

        return tuple(definition.descriptor for definition in self.load_definitions(path))

    def load_definitions(self, path: str) -> tuple[CommandDefinition, ...]:
        """Load complete command runtime definitions."""

        file_path = Path(path)
        if file_path.is_dir():
            definitions: list[CommandDefinition] = []
            for kdl_file in self._discover_command_files(file_path):
                lines = self._normalize_lines(kdl_file.read_text(encoding="utf-8"))
                definitions.extend(self._parse_commands(lines))
            return tuple(definitions)
        if file_path.suffix != ".kdl":
            raise DomainError("Command config file must use .kdl extension.", "COMMAND_CONFIG_EXT_INVALID")
        lines = self._normalize_lines(file_path.read_text(encoding="utf-8"))
        return tuple(self._parse_commands(lines))

    def _discover_command_files(self, root_directory: Path) -> tuple[Path, ...]:
        """Discover command KDL files in directory excluding example sample.

        Args:
            root_directory: Directory containing command KDL files.

        Returns:
            Sorted tuple of KDL file paths.

        Raises:
            DomainError: If no command files are found.
        """

        files = tuple(
            path
            for path in sorted(root_directory.glob("*.kdl"))
            if path.name != "example.kdl"
        )
        if not files:
            raise DomainError("No command KDL files found in directory.", "COMMAND_CONFIG_NOT_FOUND")
        return files

    def _normalize_lines(self, content: str) -> list[str]:
        result: list[str] = []
        for line in content.splitlines():
            prepared = line.split("<-")[0].split("//")[0].strip()
            if prepared:
                result.append(prepared)
        return result

    def _parse_commands(self, lines: list[str]) -> list[CommandDefinition]:
        index = 0
        definitions: list[CommandDefinition] = []
        while index < len(lines):
            name_match = re.fullmatch(r'name\s+"([a-z0-9._-]+)"', lines[index])
            if name_match is None:
                raise DomainError(f"Expected command name declaration: {lines[index]}", "COMMAND_CONFIG_PARSE_ERROR")
            command_name = name_match.group(1)
            index += 1
            description = ""
            categories: tuple[str, ...] = tuple()
            root_execute = CommandActionBlock()
            root_except: tuple[CommandExceptRule, ...] = tuple()
            subcommands: list[tuple[str, CommandScript]] = []
            while index < len(lines):
                line = lines[index]
                description_match = re.fullmatch(r'description\s+"([^"]+)"', line)
                if description_match is not None:
                    description = description_match.group(1)
                    index += 1
                    continue
                if re.fullmatch(r'category\s*=\s*\[.*\]', line):
                    categories = tuple(
                        token.strip().strip('"')
                        for token in line.split("[", maxsplit=1)[1].rstrip("]").split(",")
                        if token.strip()
                    )
                    index += 1
                    continue
                if line == "execute {":
                    root_execute, root_except, index = self._parse_execution_container(lines, index + 1)
                    continue
                subcommand_match = re.fullmatch(r'name\.([a-z0-9._-]+)\s*\{', line)
                if subcommand_match is not None:
                    script, index = self._parse_subcommand(lines, index + 1, command_name, subcommand_match.group(1))
                    subcommands.append((subcommand_match.group(1), script))
                    continue
                if line.startswith('name "'):
                    break
                raise DomainError(f"Unsupported command config line: {line}", "COMMAND_CONFIG_PARSE_ERROR")
            if not description:
                raise DomainError(f"Missing description for command: {command_name}", "COMMAND_CONFIG_MISSING_HELP")
            definitions.append(
                CommandDefinition(
                    descriptor=CommandDescriptor(
                        name=command_name,
                        required_tag=f"command.{command_name}",
                        description=description,
                        categories=categories,
                    ),
                    root_execute=root_execute,
                    root_except_rules=root_except,
                    subcommands=tuple(subcommands),
                )
            )
        return definitions

    def _parse_subcommand(
        self,
        lines: list[str],
        start_index: int,
        command_name: str,
        subcommand_name: str,
    ) -> tuple[CommandScript, int]:
        index = start_index
        description = ""
        execute = CommandActionBlock()
        except_rules: tuple[CommandExceptRule, ...] = tuple()
        while index < len(lines):
            line = lines[index]
            description_match = re.fullmatch(r'description\s+"([^"]+)"', line)
            if description_match is not None:
                description = description_match.group(1)
                index += 1
                continue
            if line == "execute {":
                execute, except_rules, index = self._parse_execution_container(lines, index + 1)
                continue
            if line == "except {":
                except_rules, index = self._parse_except_block(lines, index + 1)
                continue
            if line == "}":
                return (
                    CommandScript(
                        name=f"{command_name}.{subcommand_name}",
                        help_text=description or f"{command_name} {subcommand_name}",
                        categories=tuple(),
                        execute=execute,
                        except_rules=except_rules,
                    ),
                    index + 1,
                )
            raise DomainError(f"Invalid subcommand block line: {line}", "COMMAND_CONFIG_PARSE_ERROR")
        raise DomainError("Unclosed subcommand block.", "COMMAND_CONFIG_BLOCK_UNCLOSED")

    def _parse_execution_container(
        self,
        lines: list[str],
        start_index: int,
    ) -> tuple[CommandActionBlock, tuple[CommandExceptRule, ...], int]:
        execute, index = self._parse_action_block(lines, start_index)
        except_rules: tuple[CommandExceptRule, ...] = tuple()
        if index < len(lines) and lines[index] == "except {":
            except_rules, index = self._parse_except_block(lines, index + 1)
        return execute, except_rules, index

    def _parse_action_block(self, lines: list[str], start_index: int) -> tuple[CommandActionBlock, int]:
        stream = False
        statuses: list[tuple[str, str]] = []
        prints: list[str] = []
        command_template: str | None = None
        index = start_index
        while index < len(lines):
            line = lines[index]
            if line == "}":
                return (
                    CommandActionBlock(
                        stream=stream,
                        statuses=tuple(statuses),
                        prints=tuple(prints),
                        command_template=command_template,
                    ),
                    index + 1,
                )
            stream_match = re.fullmatch(r"stream\s+(true|false)", line)
            if stream_match is not None:
                stream = stream_match.group(1) == "true"
                index += 1
                continue
            status_match = re.fullmatch(r'status\.([a-z0-9._-]+)\s+"([^"]+)"', line)
            if status_match is not None:
                statuses.append((status_match.group(1), status_match.group(2)))
                index += 1
                continue
            print_match = re.fullmatch(r'print\s+"([^"]+)"', line)
            if print_match is not None:
                prints.append(print_match.group(1))
                index += 1
                continue
            command_match = re.fullmatch(r'command\s+"([^"]+)"', line)
            if command_match is not None:
                command_template = command_match.group(1)
                index += 1
                continue
            raise DomainError(f"Invalid execute block line: {line}", "COMMAND_CONFIG_EXEC_PARSE_ERROR")
        raise DomainError("Unclosed execute block.", "COMMAND_CONFIG_BLOCK_UNCLOSED")

    def _parse_except_block(self, lines: list[str], start_index: int) -> tuple[tuple[CommandExceptRule, ...], int]:
        rules: list[CommandExceptRule] = []
        index = start_index
        pending_code: str | None = None
        while index < len(lines):
            line = lines[index]
            if line == "}":
                return tuple(rules), index + 1
            code_match = re.fullmatch(r'code\s+"([^"]+)"', line)
            if code_match is not None:
                pending_code = code_match.group(1)
                index += 1
                continue
            if line == "code.execute {":
                if pending_code is None:
                    raise DomainError("code.execute requires previous code.", "COMMAND_CONFIG_CODE_ORDER_ERROR")
                execute, index = self._parse_action_block(lines, index + 1)
                rules.append(CommandExceptRule(expression=pending_code, execute=execute))
                pending_code = None
                continue
            raise DomainError(f"Invalid except block line: {line}", "COMMAND_CONFIG_EXCEPT_PARSE_ERROR")
        raise DomainError("Unclosed except block.", "COMMAND_CONFIG_BLOCK_UNCLOSED")
