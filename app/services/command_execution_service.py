import queue
import shlex
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Generator

import paramiko

from app.config import get_settings


@dataclass(frozen=True)
class CommandExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    duration_seconds: float


class CommandExecutionService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def run_command(
        self,
        command: list[str],
        timeout_seconds: int,
        file_not_found_message: str,
        timeout_message: str,
    ) -> CommandExecutionResult:
        if self.settings.execution_mode == "ssh":
            return self._run_ssh_command(command, timeout_seconds, timeout_message)
        return self._run_local_command(command, timeout_seconds, file_not_found_message, timeout_message)

    def stream_command(
        self,
        command: list[str],
        timeout_seconds: int,
        file_not_found_message: str,
        timeout_message: str,
    ) -> Generator[dict[str, object], None, None]:
        if self.settings.execution_mode == "ssh":
            yield from self._stream_ssh_command(command, timeout_seconds, timeout_message)
            return
        yield from self._stream_local_command(command, timeout_seconds, file_not_found_message, timeout_message)

    def _run_local_command(
        self,
        command: list[str],
        timeout_seconds: int,
        file_not_found_message: str,
        timeout_message: str,
    ) -> CommandExecutionResult:
        result: CommandExecutionResult | None = None
        for event in self._stream_local_command(command, timeout_seconds, file_not_found_message, timeout_message):
            if event["type"] == "result":
                result = event["result"]  # type: ignore[assignment]

        if result is None:
            raise RuntimeError("Execution locale incomplete.")
        return result

    def _stream_local_command(
        self,
        command: list[str],
        timeout_seconds: int,
        file_not_found_message: str,
        timeout_message: str,
    ) -> Generator[dict[str, object], None, None]:
        started_at = time.perf_counter()
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError:
            raise RuntimeError(file_not_found_message)
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        event_queue: queue.Queue[tuple[str, str] | tuple[str, None]] = queue.Queue()

        def pipe_reader(stream_name: str, stream) -> None:
            try:
                for line in iter(stream.readline, ""):
                    event_queue.put((stream_name, line.rstrip("\r\n")))
            finally:
                stream.close()
                event_queue.put((f"{stream_name}_done", None))

        stdout_thread = threading.Thread(target=pipe_reader, args=("stdout", process.stdout), daemon=True)
        stderr_thread = threading.Thread(target=pipe_reader, args=("stderr", process.stderr), daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        remaining_streams = {"stdout", "stderr"}

        try:
            while remaining_streams:
                if time.perf_counter() - started_at > timeout_seconds:
                    process.kill()
                    raise RuntimeError(timeout_message)

                try:
                    stream_name, payload = event_queue.get(timeout=0.2)
                except queue.Empty:
                    if process.poll() is not None and not stdout_thread.is_alive() and not stderr_thread.is_alive():
                        break
                    continue

                if stream_name.endswith("_done"):
                    remaining_streams.discard(stream_name.replace("_done", ""))
                    continue

                if payload is None:
                    continue

                if stream_name == "stdout":
                    stdout_lines.append(payload)
                else:
                    stderr_lines.append(payload)
                yield {"type": stream_name, "line": payload}
        finally:
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            process.wait(timeout=5)

        yield {
            "type": "result",
            "result": CommandExecutionResult(
                stdout="\n".join(stdout_lines).strip(),
                stderr="\n".join(stderr_lines).strip(),
                exit_code=process.returncode or 0,
                duration_seconds=round(time.perf_counter() - started_at, 2),
            ),
        }

    def _run_ssh_command(
        self,
        command: list[str],
        timeout_seconds: int,
        timeout_message: str,
    ) -> CommandExecutionResult:
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        result: CommandExecutionResult | None = None

        for event in self._stream_ssh_command(command, timeout_seconds, timeout_message):
            if event["type"] == "stdout":
                stdout_lines.append(str(event["line"]))
            elif event["type"] == "stderr":
                stderr_lines.append(str(event["line"]))
            elif event["type"] == "result":
                result = event["result"]  # type: ignore[assignment]

        if result is not None:
            return result

        return CommandExecutionResult(
            stdout="\n".join(stdout_lines).strip(),
            stderr="\n".join(stderr_lines).strip(),
            exit_code=1,
            duration_seconds=0.0,
        )

    def _stream_ssh_command(
        self,
        command: list[str],
        timeout_seconds: int,
        timeout_message: str,
    ) -> Generator[dict[str, object], None, None]:
        client = self._build_ssh_client()
        command_string = shlex.join(command)
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        stdout_buffer = ""
        stderr_buffer = ""
        started_at = time.perf_counter()

        try:
            client.connect(
                hostname=self.settings.kali_ssh_host,
                port=self.settings.kali_ssh_port,
                username=self.settings.kali_ssh_username,
                password=self.settings.kali_ssh_password or None,
                key_filename=self.settings.kali_ssh_key_path or None,
                look_for_keys=not bool(self.settings.kali_ssh_password),
                allow_agent=False,
                timeout=10,
            )
            _, stdout, stderr = client.exec_command(command_string, get_pty=True)
            channel = stdout.channel

            while True:
                if time.perf_counter() - started_at > timeout_seconds:
                    channel.close()
                    raise RuntimeError(timeout_message)

                made_progress = False

                while channel.recv_ready():
                    made_progress = True
                    stdout_buffer += channel.recv(4096).decode("utf-8", errors="replace")
                    stdout_buffer, stdout_events = self._consume_complete_lines(stdout_buffer)
                    for line in stdout_events:
                        stdout_lines.append(line)
                        yield {"type": "stdout", "line": line}

                while channel.recv_stderr_ready():
                    made_progress = True
                    stderr_buffer += channel.recv_stderr(4096).decode("utf-8", errors="replace")
                    stderr_buffer, stderr_events = self._consume_complete_lines(stderr_buffer)
                    for line in stderr_events:
                        stderr_lines.append(line)
                        yield {"type": "stderr", "line": line}

                if channel.exit_status_ready() and not channel.recv_ready() and not channel.recv_stderr_ready():
                    break

                if not made_progress:
                    time.sleep(0.1)

            stdout_buffer, stdout_events = self._consume_complete_lines(stdout_buffer, flush_remainder=True)
            for line in stdout_events:
                stdout_lines.append(line)
                yield {"type": "stdout", "line": line}

            stderr_buffer, stderr_events = self._consume_complete_lines(stderr_buffer, flush_remainder=True)
            for line in stderr_events:
                stderr_lines.append(line)
                yield {"type": "stderr", "line": line}
            exit_code = channel.recv_exit_status()
        except paramiko.AuthenticationException as error:
            raise RuntimeError("Authentification SSH vers Kali echouee.") from error
        except paramiko.SSHException as error:
            raise RuntimeError(f"Connexion SSH vers Kali impossible: {error}") from error
        except OSError as error:
            raise RuntimeError(f"Connexion SSH vers Kali impossible: {error}") from error
        finally:
            client.close()

        yield {
            "type": "result",
            "result": CommandExecutionResult(
                stdout="\n".join(stdout_lines).strip(),
                stderr="\n".join(stderr_lines).strip(),
                exit_code=exit_code,
                duration_seconds=round(time.perf_counter() - started_at, 2),
            ),
        }

    def _build_ssh_client(self) -> paramiko.SSHClient:
        if not self.settings.kali_ssh_host:
            raise RuntimeError("Le mode SSH est active, mais KALI_SSH_HOST n'est pas configure.")

        client = paramiko.SSHClient()
        if self.settings.kali_ssh_allow_unknown_host:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            client.load_system_host_keys()
        return client

    def _consume_complete_lines(
        self,
        buffer: str,
        flush_remainder: bool = False,
    ) -> tuple[str, list[str]]:
        lines: list[str] = []
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            lines.append(line.rstrip("\r"))

        if flush_remainder and buffer:
            lines.append(buffer.rstrip("\r"))
            return "", lines

        return buffer, lines


command_execution_service = CommandExecutionService()
