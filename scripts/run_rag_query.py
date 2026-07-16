"""Run a local RAG query for debugging."""

import argparse
import asyncio

from onssa_ai.api.dependencies import get_rag_service
from onssa_ai.schemas.rag import RagRequest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    args = parser.parse_args()
    response = asyncio.run(get_rag_service().answer(RagRequest(question=args.question)))
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
