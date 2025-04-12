from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from elasticsearch_dsl import connections
from elasticsearch import Elasticsearch
from django.conf import settings
from .models import (
    CodeforcesProblem,CodeforcesUser
)
from .elastic import INDEX_NAME, model_to_document

# Connect to Elasticsearch
es = connections.get_connection()

def index_document(instance):
    """
    Indexes or updates a document in Elasticsearch based on the given model instance.
    """
    data = model_to_document(instance)

    model_name = instance.__class__.__name__.lower()
    doc_id = f"{model_name}_{data.get('id')}"

    if doc_id:
        es.index(index=INDEX_NAME, id=doc_id, body=data)
        print(f"Document {doc_id} indexed successfully.")
    else:
        print("Error: Missing document ID, cannot index.")


def delete_document(instance):
    """
    Deletes a document from Elasticsearch using the model instance.
    """
    model_name = instance.__class__.__name__.lower()
    doc_id = f"{model_name}_{instance.id}"

    es.delete(index=INDEX_NAME, id=doc_id, ignore=[404])
    print(f"Document {doc_id} deleted from Elasticsearch.")


@receiver(post_save, sender=CodeforcesUser)
@receiver(post_save, sender=CodeforcesProblem)
def save_to_elasticsearch(sender, instance, **kwargs):
    index_document(instance)

@receiver(post_delete, sender=CodeforcesProblem)
@receiver(post_delete, sender=CodeforcesUser)
def delete_from_elasticsearch(sender, instance, **kwargs):
    delete_document(instance)