from django.core.management.base import BaseCommand
from problems.models import CodeforcesProblem,CodeforcesUser
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk,BulkIndexError
from problems.elastic import INDEX_NAME, model_to_document

es = Elasticsearch(["http://localhost:9200"])

class Command(BaseCommand):
    help = "Indexes all existing data into Elasticsearch"

    def handle(self, *args, **kwargs):
        self.stdout.write("Indexing existing data into Elasticsearch...")

        bulk_data = []

        def index_model(model, prefix):
            """Helper function to index data from a specific model."""
            for instance in model.objects.all():
                doc = model_to_document(instance)
                # print(f"Instance: {instance}, Doc: {doc}")  # <-- Add this line
                model_name = instance.__class__.__name__.lower()
                if doc:
                    bulk_data.append({
                        "_index": INDEX_NAME,
                        "_id": f"{model_name}_{doc['id']}",  # Unique ID for each model
                        "_source": doc
                    })

        # Index each model with a unique prefix
        index_model(CodeforcesProblem, "codeforces_problems")
        index_model(CodeforcesUser, "codeforces_user")
       

        # Perform Bulk Insert
        if bulk_data:
            try:
                bulk(es, bulk_data)
                self.stdout.write(self.style.SUCCESS("Successfully indexed existing data!"))
            except BulkIndexError as e:
                self.stderr.write(self.style.ERROR(f"{len(e.errors)} document(s) failed to index."))
                for err in e.errors:
                    self.stderr.write(str(err))
        else:
            self.stdout.write(self.style.WARNING("No data found to index."))
