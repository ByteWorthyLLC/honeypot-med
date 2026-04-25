"""Domain models for prompt injection honeypot analysis."""

from dataclasses import asdict, dataclass

from .errors import ValidationError


@dataclass(frozen=True)
class InputToolCall:
    name: str
    args: str = ""

    @classmethod
    def from_dict(cls, raw: dict) -> "InputToolCall":
        if not isinstance(raw, dict):
            raise ValidationError("tool_calls entries must be objects")
        name = raw.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("tool_calls[].name must be a non-empty string")
        args = raw.get("args", "")
        if not isinstance(args, str):
            args = str(args)
        return cls(name=name.strip(), args=args)


@dataclass(frozen=True)
class InputEvent:
    prompt: str
    tool_calls: list[InputToolCall]
    model_output: str
    response: str

    @classmethod
    def from_dict(cls, raw: dict) -> "InputEvent":
        if not isinstance(raw, dict):
            raise ValidationError("events entries must be objects")

        prompt = raw.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValidationError("events[].prompt must be a non-empty string")

        tool_calls_raw = raw.get("tool_calls", [])
        if not isinstance(tool_calls_raw, list):
            raise ValidationError("events[].tool_calls must be a list")
        tool_calls = [InputToolCall.from_dict(item) for item in tool_calls_raw]

        model_output = raw.get("model_output", "")
        response = raw.get("response", "")
        if not isinstance(model_output, str):
            model_output = str(model_output)
        if not isinstance(response, str):
            response = str(response)

        return cls(
            prompt=prompt.strip(),
            tool_calls=tool_calls,
            model_output=model_output,
            response=response,
        )


@dataclass(frozen=True)
class InputPayload:
    events: list[InputEvent]

    @classmethod
    def from_dict(cls, raw: dict) -> "InputPayload":
        if not isinstance(raw, dict):
            raise ValidationError("Input payload must be a JSON object.")

        if "events" in raw:
            events_raw = raw.get("events")
            if not isinstance(events_raw, list):
                raise ValidationError("Field 'events' must be a list.")
            events = [InputEvent.from_dict(item) for item in events_raw]
            if not events:
                raise ValidationError("Field 'events' must not be empty.")
            return cls(events=events)

        # Backward compatibility with older payload shape.
        prompts = raw.get("prompts")
        if isinstance(prompts, list):
            events = []
            for idx, prompt in enumerate(prompts):
                if not isinstance(prompt, str) or not prompt.strip():
                    raise ValidationError(f"prompts[{idx}] must be a non-empty string.")
                events.append(InputEvent(prompt=prompt.strip(), tool_calls=[], model_output="", response=""))
            if not events:
                raise ValidationError("Field 'prompts' must not be empty.")
            return cls(events=events)

        raise ValidationError("Payload must contain either 'events' or 'prompts'.")


@dataclass(frozen=True)
class DetectionFinding:
    rule_id: str
    attack_family: str
    hit: str
    proven: bool
    evidence: list[str]
    score: int
    severity: str

    def to_dict(self) -> dict:
        return asdict(self)
