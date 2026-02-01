"""
Script de test pour l'API de recherche de clients
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Affiche un titre de section"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_create_sample_clients():
    """Crée des clients de test"""
    print_section("Création de clients de test")
    
    clients = [
        {
            "client_number": "CLI-2024-001",
            "client_type": "entreprise",
            "company_name": "Entreprise Dupont",
            "email": "contact@dupont.fr",
            "phone": "0123456789",
            "address_line1": "10 rue de la Paix",
            "postal_code": "75001",
            "city": "Paris"
        },
        {
            "client_number": "CLI-2024-002",
            "client_type": "entreprise",
            "company_name": "Construction Dubois",
            "email": "info@dubois.fr",
            "phone": "0123456790",
            "address_line1": "20 avenue Victor Hugo",
            "postal_code": "69001",
            "city": "Lyon"
        },
        {
            "client_number": "CLI-2024-003",
            "client_type": "particulier",
            "first_name": "Jean",
            "last_name": "Martin",
            "email": "jean.martin@email.fr",
            "phone": "0612345678",
            "address_line1": "5 place de la République",
            "postal_code": "13001",
            "city": "Marseille"
        },
        {
            "client_number": "CLI-2024-004",
            "client_type": "particulier",
            "first_name": "Marie",
            "last_name": "Dupond",  # Variante orthographique de Dupont
            "email": "marie.dupond@email.fr",
            "phone": "0612345679",
            "address_line1": "15 rue du Commerce",
            "postal_code": "33000",
            "city": "Bordeaux"
        },
        {
            "client_number": "CLI-2024-005",
            "client_type": "entreprise",
            "company_name": "Maçonnerie Bernard",
            "email": "contact@bernard.fr",
            "phone": "0123456791",
            "address_line1": "8 boulevard des Artisans",
            "postal_code": "44000",
            "city": "Nantes"
        }
    ]
    
    created_count = 0
    for client in clients:
        try:
            response = requests.post(f"{BASE_URL}/clients/", json=client)
            if response.status_code == 201:
                created_count += 1
                print(f"✅ Client créé: {client['client_number']}")
            elif response.status_code == 400:
                print(f"⚠️  Client existe déjà: {client['client_number']}")
            else:
                print(f"❌ Erreur {response.status_code}: {client['client_number']}")
        except Exception as e:
            print(f"❌ Erreur lors de la création: {e}")
    
    print(f"\n{created_count} nouveaux clients créés")

def test_search_by_number():
    """Test de recherche par numéro"""
    print_section("Test: Recherche par numéro exact")
    
    test_number = "CLI-2024-001"
    response = requests.get(f"{BASE_URL}/clients/search?query={test_number}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Recherche de '{test_number}'")
        print(f"   Résultats trouvés: {len(results)}")
        for client in results:
            name = client.get('company_name') or f"{client.get('first_name')} {client.get('last_name')}"
            print(f"   - {client['client_number']}: {name}")
    else:
        print(f"❌ Erreur {response.status_code}")

def test_search_by_company_name():
    """Test de recherche par nom d'entreprise"""
    print_section("Test: Recherche par nom d'entreprise")
    
    query = "Construction"
    response = requests.get(f"{BASE_URL}/clients/search?query={query}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Recherche de '{query}'")
        print(f"   Résultats trouvés: {len(results)}")
        for client in results:
            print(f"   - {client['client_number']}: {client.get('company_name', 'N/A')}")
    else:
        print(f"❌ Erreur {response.status_code}")

def test_search_by_last_name():
    """Test de recherche par nom de famille"""
    print_section("Test: Recherche par nom de famille")
    
    query = "Martin"
    response = requests.get(f"{BASE_URL}/clients/search?query={query}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Recherche de '{query}'")
        print(f"   Résultats trouvés: {len(results)}")
        for client in results:
            if client.get('last_name'):
                print(f"   - {client['client_number']}: {client['first_name']} {client['last_name']}")
    else:
        print(f"❌ Erreur {response.status_code}")

def test_phonetic_search():
    """Test de recherche phonétique"""
    print_section("Test: Recherche phonétique")
    
    # Test 1: Dupont vs Dupond
    print("\n🔍 Test phonétique: 'Dupont' (devrait trouver 'Dupond')")
    response = requests.get(f"{BASE_URL}/clients/search?query=Dupont&phonetic=true")
    
    if response.status_code == 200:
        results = response.json()
        print(f"   Résultats trouvés: {len(results)}")
        for client in results:
            name = client.get('company_name') or f"{client.get('first_name', '')} {client.get('last_name', '')}"
            print(f"   - {client['client_number']}: {name}")
    else:
        print(f"❌ Erreur {response.status_code}")
    
    # Test 2: Dubois vs Duboit
    print("\n🔍 Test phonétique: 'Duboit' (devrait trouver 'Dubois')")
    response = requests.get(f"{BASE_URL}/clients/search?query=Duboit&phonetic=true")
    
    if response.status_code == 200:
        results = response.json()
        print(f"   Résultats trouvés: {len(results)}")
        for client in results:
            name = client.get('company_name') or f"{client.get('first_name', '')} {client.get('last_name', '')}"
            print(f"   - {client['client_number']}: {name}")
    else:
        print(f"❌ Erreur {response.status_code}")
    
    # Test 3: Bernard vs Bernar
    print("\n🔍 Test phonétique: 'Bernar' (devrait trouver 'Bernard')")
    response = requests.get(f"{BASE_URL}/clients/search?query=Bernar&phonetic=true")
    
    if response.status_code == 200:
        results = response.json()
        print(f"   Résultats trouvés: {len(results)}")
        for client in results:
            name = client.get('company_name') or f"{client.get('first_name', '')} {client.get('last_name', '')}"
            print(f"   - {client['client_number']}: {name}")
    else:
        print(f"❌ Erreur {response.status_code}")

def test_search_with_partial_match():
    """Test de recherche avec correspondance partielle"""
    print_section("Test: Recherche partielle")
    
    query = "Dup"
    response = requests.get(f"{BASE_URL}/clients/search?query={query}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Recherche de '{query}' (partiel)")
        print(f"   Résultats trouvés: {len(results)}")
        for client in results:
            name = client.get('company_name') or f"{client.get('first_name', '')} {client.get('last_name', '')}"
            print(f"   - {client['client_number']}: {name}")
    else:
        print(f"❌ Erreur {response.status_code}")

def main():
    """Fonction principale"""
    print("\n" + "🧪 TEST DE L'API DE RECHERCHE DE CLIENTS ".center(60, "="))
    
    try:
        # Vérifier que le serveur est accessible
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            print(f"\n❌ Le serveur n'est pas accessible sur {BASE_URL}")
            print("   Assurez-vous que le serveur FastAPI est démarré avec: python main.py")
            return
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Impossible de se connecter au serveur sur {BASE_URL}")
        print("   Assurez-vous que le serveur FastAPI est démarré avec: python main.py")
        return
    
    # Créer des clients de test
    test_create_sample_clients()
    
    # Tests de recherche
    test_search_by_number()
    test_search_by_company_name()
    test_search_by_last_name()
    test_search_with_partial_match()
    test_phonetic_search()
    
    print("\n" + "="*60)
    print("  ✅ Tests terminés")
    print("="*60)
    print(f"\n📚 Documentation interactive: {BASE_URL}/docs")
    print(f"   Testez l'endpoint: GET /clients/search\n")

if __name__ == "__main__":
    main()
