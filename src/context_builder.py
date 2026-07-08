from collections import defaultdict


class ContextBuilder:

    def build(self, results):

        grouped = defaultdict(list)

        # Group retrieved chunks by source document
        for result in results:
            chunk = result["chunk"]
            grouped[chunk.metadata.file_name].append(result)

        context = []

        for file_name, items in grouped.items():

            # Sort chunks within the document by retrieval score
            items.sort(
                key=lambda item: item["score"],
                reverse=True
            )

            context.append({
                "source": file_name,
                "best_score": max(item["score"] for item in items),
                "chunks": items
            })

        # Sort documents by best retrieval score
        context.sort(
            key=lambda doc: doc["best_score"],
            reverse=True
        )

        return context