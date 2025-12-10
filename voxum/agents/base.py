"""Base agent class/interface."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


@dataclass
class AgentResult(Generic[OutputT]):
    """Result from an agent execution."""

    success: bool
    output: OutputT | None
    error: str | None = None


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all pipeline agents.

    Each agent processes an input and produces an output.
    Agents handle their own logging and error handling.
    """

    def __init__(self, name: str | None = None):
        """Initialize the agent.

        Args:
            name: Optional name for the agent (defaults to class name)
        """
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"voxum.agents.{self.name}")

    @abstractmethod
    def _process(self, input_data: InputT) -> OutputT:
        """Process the input and return output.

        Override this method in subclasses.

        Args:
            input_data: Input for the agent

        Returns:
            Processed output
        """
        pass

    def process(self, input_data: InputT) -> AgentResult[OutputT]:
        """Execute the agent's processing with error handling.

        Args:
            input_data: Input for the agent

        Returns:
            AgentResult with success status and output or error
        """
        self.logger.info(f"Starting {self.name}")

        try:
            output = self._process(input_data)
            self.logger.info(f"{self.name} completed successfully")
            return AgentResult(success=True, output=output)
        except Exception as e:
            self.logger.error(f"{self.name} failed: {e}", exc_info=True)
            return AgentResult(success=False, output=None, error=str(e))

    def load_prompt(self, prompt_name: str) -> str:
        """Load a prompt template from the prompts directory.

        Args:
            prompt_name: Name of the prompt file (without .txt extension)

        Returns:
            Prompt template string
        """
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_dir / f"{prompt_name}.txt"

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        return prompt_file.read_text().strip()
