import typer

MIN_PERSONA_ID = 1
MAX_PERSONA_ID = 100


class PersonaRange:
    min_id: int
    max_id: int

    def __init__(self, min_id: int = MIN_PERSONA_ID, max_id: int = MAX_PERSONA_ID):
        self.min_id = max(min_id, MIN_PERSONA_ID)
        self.max_id = min(max_id, MAX_PERSONA_ID)

    @property
    def full_range(self) -> bool:
        return self.min_id == MIN_PERSONA_ID and self.max_id == MAX_PERSONA_ID

    def range(self) -> range:
        return range(self.min_id, self.max_id + 1)


def parse_persona_range(value: str | PersonaRange) -> PersonaRange:
    if isinstance(value, PersonaRange):
        return value
    if "-" in value:
        parts = value.split("-")
        if len(parts) != 2:
            raise typer.BadParameter(
                "Persona range must be in the format 'min-max' or a single integer."
            )
        if parts[0] == "":
            min_id = MIN_PERSONA_ID
        else:
            try:
                min_id = int(parts[0])
            except ValueError:
                raise typer.BadParameter("Persona range values must be integers.")

        if parts[1] == "":
            max_id = MAX_PERSONA_ID
        else:
            try:
                max_id = int(parts[1])
            except ValueError:
                raise typer.BadParameter("Persona range values must be integers.")

        if min_id > max_id:
            raise typer.BadParameter(
                "Minimum persona ID cannot be greater than maximum persona ID."
            )
        return PersonaRange(min_id=min_id, max_id=max_id)
    else:
        if value == "all":
            return PersonaRange(min_id=MIN_PERSONA_ID, max_id=MAX_PERSONA_ID)
        try:
            identifier = int(value)
        except ValueError:
            raise typer.BadParameter("Persona identifier must be an integer.")
        return PersonaRange(min_id=identifier, max_id=identifier)
