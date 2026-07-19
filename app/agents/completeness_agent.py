class CompletenessAgent:
    name = "completeness_agent"

    def run(self, metadata: dict, doc_type: str) -> dict:
        missing = metadata.get("missing_fields", [])
        print(type(missing))
        print(missing)
        is_complete = len(missing) == 0

        if is_complete:
            recommendation = f"Document appears complete for type '{doc_type}'. Safe to route for automated processing."
        else:
            recommendation = (
                f"Document of type '{doc_type}' is missing: {', '.join(missing)}. "
                f"Recommend routing back for manual review before automated processing."
            )

        return {
            "agent": self.name,
            "doc_type": doc_type,
            "is_complete": is_complete,
            "missing_fields": missing,
            "recommendation": recommendation,
        }
