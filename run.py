from neo4j import GraphDatabase
from neo4j_graphrag.indexes import (
    create_vector_index,
    create_fulltext_index,
    drop_index_if_exists,
    upsert_vectors
)

# Configure your Neo4j connection details
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

# Index configuration
VECTOR_INDEX_NAME = "product_embeddings"
FULLTEXT_INDEX_NAME = "product_names"
EMBEDDING_PROPERTY = "embedding"
VECTOR_DIMENSIONS = 3  

def create_sample_graph(tx):
   
    tx.run("MATCH (n) DETACH DELETE n")
    
   
    tx.run("""
        CREATE (alice:Person {name: 'Alice'})
        CREATE (bob:Person {name: 'Bob'})
        CREATE (charlie:Person {name: 'Charlie'})
        
        CREATE (laptop:Product {name: 'Laptop', price: 1200})
        CREATE (phone:Product {name: 'Phone', price: 800})
        CREATE (tablet:Product {name: 'Tablet', price: 600})
        
        CREATE (alice)-[:BOUGHT]->(laptop)
        CREATE (alice)-[:BOUGHT]->(phone)
        CREATE (bob)-[:BOUGHT]->(phone)
        CREATE (bob)-[:BOUGHT]->(tablet)
        CREATE (charlie)-[:BOUGHT]->(laptop)
        CREATE (charlie)-[:BOUGHT]->(tablet)
    """)

def get_product_ids(tx):
    result = tx.run("MATCH (p:Product) RETURN id(p) AS id")
    return [record["id"] for record in result]

def main():
    driver = GraphDatabase.driver(URI, auth=AUTH, encrypted=False)
    
    try:
        driver.verify_connectivity()
        
        with driver.session() as session:
           
            session.execute_write(create_sample_graph)
            print("Created base graph structure")
            
          
            product_ids = session.execute_read(get_product_ids)
            print(f"Retrieved product IDs: {product_ids}")
            
            # Generate sample embeddings (replace with real embeddings in production)
            embeddings = [
                [0.12, 0.34, 0.56],  # Laptop
                [0.78, 0.90, 0.12],  # Phone
                [0.34, 0.56, 0.78]   # Tablet
            ]
            
           
            upsert_vectors(
                driver=driver,
                ids=product_ids,
                embedding_property=EMBEDDING_PROPERTY,
                embeddings=embeddings,
                entity_type='NODE'
            )
            print("Added vector embeddings to products")
            
            
            drop_index_if_exists(driver, VECTOR_INDEX_NAME)
            create_vector_index(
                driver,
                name=VECTOR_INDEX_NAME,
                label="Product",
                embedding_property=EMBEDDING_PROPERTY,
                dimensions=VECTOR_DIMENSIONS,
                similarity_fn="cosine"
            )
            
            drop_index_if_exists(driver, FULLTEXT_INDEX_NAME)
            create_fulltext_index(
                driver,
                name=FULLTEXT_INDEX_NAME,
                label="Product",
                node_properties=["name"]
            )
            print("Created vector and fulltext indexes")
            
        print("Graph creation and indexing completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()
