# examples/advanced_search_example.py
import asyncio
from viper_logs import AdvancedLogger
from datetime import datetime

def print_results(results, display_config=None):
    """
    Affiche les résultats de recherche de manière formatée.
    
    Args:
        results: Liste des résultats de recherche
        display_config: Configuration d'affichage optionnelle pour le tableau formaté
    """
    if not results:
        print("Aucun résultat trouvé")
        return
    
    print(f"Nombre de résultats: {len(results)}")
    
    # Afficher le tableau formaté si display_config est fourni
    if display_config:
        print(display_config.format_log_table(results))
    
    print("\nDétails des résultats:")
    for result in results:
        timestamp = datetime.fromtimestamp(result['timestamp'])
        score = f" (score: {result['score']:.2f})" if 'score' in result else ""
        print(f"- [{timestamp}] {result['level']}: {result['description']}{score}")
        print(f"  ID: {result['id']}, Action: {result['action']}")

async def main():
    # Initialisation du logger
    logger = AdvancedLogger("search_demo")
    
    # Attendre un peu pour s'assurer que le logger est initialisé
    await asyncio.sleep(0.1)
    
    print("\nCréation des logs de test...")
    
    # Logs de test variés
    test_logs = [
        {
            "level": "ERROR",
            "user_id": "user123",
            "action": "login",
            "description": "Failed login attempt from IP 192.168.1.1",
            "component": "auth",
            "metadata": {"ip": "192.168.1.1"}
        },
        {
            "level": "INFO",
            "user_id": "user456",
            "action": "login",
            "description": "Successful login",
            "component": "auth",
            "metadata": {}
        },
        {
            "level": "WARN",
            "user_id": "user789",
            "action": "logout",
            "description": "Session timeout during logout",
            "component": "auth",
            "metadata": {"session_duration": "3600"}
        },
        {
            "level": "ERROR",
            "user_id": "user123",
            "action": "authentication",
            "description": "Login failed: invalid credentials",
            "component": "auth",
            "metadata": {"attempt": 2}
        }
    ]

    # Création des logs
    for log_data in test_logs:
        await logger.log(
            log_data["level"],
            log_data["user_id"],
            log_data["action"],
            log_data["description"],
            log_data["component"],
            log_data["metadata"]
        )
        # Petit délai pour assurer l'ordre
        await asyncio.sleep(0.1)

    try:
        # Test 1: Recherche standard
        print("\n1. Recherche standard")
        print("Recherche des logs contenant 'login':")
        query = logger.search().containing("login")
        results = await logger.execute_search(query)
        print_results(results, logger.display_config)
        
        # Test 2: Recherche fuzzy
        print("\n2. Recherche fuzzy")
        fuzzy_terms = ["logn", "lgin", "authn", "logout"]
        for term in fuzzy_terms:
            print(f"\nRecherche fuzzy pour '{term}' (seuil: 0.6):")
            results = await logger.fuzzy_search(term, threshold=0.6)
            print_results(results, logger.display_config)
        
        # Test 3: Recherche booléenne
        print("\n3. Recherche booléenne")
        boolean_queries = [
            "ERROR AND login",
            "login OR logout",
            "ERROR AND NOT logout"
        ]
        for query in boolean_queries:
            print(f"\nRecherche booléenne pour '{query}':")
            results = await logger.boolean_search(query)
            print_results(results, logger.display_config)

    except Exception as e:
        print(f"Erreur lors des tests: {str(e)}")
    
    finally:
        # Nettoyage
        await logger.close()

if __name__ == "__main__":
    asyncio.run(main())