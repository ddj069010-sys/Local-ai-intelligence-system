
class ResponsePipeline:
    def __init__(self, generator, validator, formatter):
        self.generator = generator
        self.validator = validator
        self.formatter = formatter

    async def run(self, question, model, system, images=None):
        # STEP 1: Generate
        raw = ""
        async for token in self.generator(question, model, system=system, images=images):
            if isinstance(token, dict):
                raw += token.get("text", "")
            else:
                raw += str(token)

        # STEP 2: Validate (small model)
        validated = await self.validator(raw)

        # STEP 3: Format
        final = await self.formatter(validated)

        yield {"type": "message", "text": final}
