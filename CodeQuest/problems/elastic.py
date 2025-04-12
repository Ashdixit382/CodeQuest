from elasticsearch_dsl import Document, Text, Integer,Object,Keyword
from elasticsearch_dsl.connections import connections
from .models import CodeforcesProblem
from django.conf import settings

connections.create_connection(
    alias="default",
    hosts=settings.ELASTICSEARCH_DSL['default']['hosts']
)
es = connections.get_connection()
INDEX_NAME = "problems"


class ProblemDocument(Document):
    
    # codeforces_problems model
    codeforces_problems = Object(properties={
        "id": Integer(),
        "type": Keyword(),

        "contest_id": Integer(),
        "index": Text(),  
        
        "name": Text(),  
        "rating": Integer(), 
        "url": Keyword(),  
    })

    #codeforces_users
    codeforces_user = Object(properties={
        "id":Integer(),
        "type":Keyword(),

        "handle": Keyword(),
        "solved_problems": Integer(multi=True)
    })


    class Index:
        name = 'problems'
        settings = {
            "number_of_shards": 3,
            "number_of_replicas": 1
        }
    


def model_to_document(instance):
    """
    Converts a Django model instance into an Elasticsearch document format.
    """
    model_name = instance.__class__.__name__.lower()  # Get model type dynamically

    if model_name == "codeforcesproblem":
        return {
            "id": instance.id,
            "type": "codeforcesproblem",  

            "contest_id": instance.contest_id,
            "index": instance.index,
            "name": instance.name,
            "rating": instance.rating,
            "url": instance.url
        }
    
    elif model_name == "codeforcesuser":
        return {
            "id": instance.id,
            "type": "codeforcesuser",  # ✅ Correct type
            "handle": instance.handle,
            "solved_problems": [problem.id for problem in instance.solved_problems.all()]  # ✅ correct key name
        }

# Create the index
def create_index():
    if not ProblemDocument._index.exists():
        ProblemDocument.init()
        print(f"Index '{INDEX_NAME}' created successfully.")
    else:
        print(f"Index '{INDEX_NAME}' already exists.")

create_index()