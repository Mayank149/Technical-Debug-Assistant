from src.embedder import Embedder
from src.vector_store import VectorStore
from src.context_builder import ContextBuilder
from src.prompt_builder import PromptBuilder
from src.generator import Generator


def print_sources(context):

    print("\n" + "=" * 80)
    print("SOURCES")
    print("=" * 80)

    for document in context:

        print(
            f"\n📄 {document['source']} "
            f"(score: {document['best_score']:.3f})"
        )

        seen = set()

        for item in document["chunks"]:

            heading = item["chunk"].metadata.heading

            if heading not in seen:
                print(f"   • {heading}")
                seen.add(heading)


def main():

    embedder = Embedder()

    vector_store = VectorStore()
    vector_store.load_index()

    context_builder = ContextBuilder()
    prompt_builder = PromptBuilder()

    generator = Generator()

    while True:

        print("\n" + "=" * 80)

        question = input("Ask a question (or 'exit'): ")

        if question.lower() == "exit":
            break

        # Query embedding
        query_embedding = embedder.embed_text(question)

        # Retrieve
        results = vector_store.search(query_embedding, top_k=5)

        # Build structured context
        context = context_builder.build(results)

        # Build prompt
        prompt = prompt_builder.build(context, question)

        # Generate answer
        answer = generator.generate(prompt)

        print("\n" + "=" * 80)
        print("ANSWER")
        print("=" * 80)
        print(answer)

        print_sources(context)


if __name__ == "__main__":
    main()