"""Script de test rapide de l'API"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_api():
    """Teste les endpoints principaux de l'API"""
    
    print("=" * 70)
    print("  Tests de l'API Gestion Assurance Construction")
    print("=" * 70)
    
    # Test 1 : Root endpoint
    print("\n1️⃣  Test du endpoint root...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2 : Health check
    print("\n2️⃣  Test du health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3 : Liste des types de contrats
    print("\n3️⃣  Test de la liste des types de contrats...")
    try:
        response = requests.get(f"{BASE_URL}/referentials/contract-types")
        print(f"   ✅ Status: {response.status_code}")
        data = response.json()
        print(f"   📊 Nombre de types de contrats: {len(data)}")
        if data:
            print(f"   📄 Premier type: {data[0]['code']} - {data[0]['name']}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 4 : Liste des garanties
    print("\n4️⃣  Test de la liste des garanties...")
    try:
        response = requests.get(f"{BASE_URL}/referentials/guarantees")
        print(f"   ✅ Status: {response.status_code}")
        data = response.json()
        print(f"   📊 Nombre de garanties: {len(data)}")
        if data:
            print(f"   📄 Première garantie: {data[0]['code']} - {data[0]['name']}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 5 : Liste des professions
    print("\n5️⃣  Test de la liste des professions...")
    try:
        response = requests.get(f"{BASE_URL}/referentials/professions")
        print(f"   ✅ Status: {response.status_code}")
        data = response.json()
        print(f"   📊 Nombre de professions: {len(data)}")
        if data:
            print(f"   📄 Première profession: {data[0]['code']} - {data[0]['name']}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 6 : Créer un client test
    print("\n6️⃣  Test de création d'un client...")
    try:
        client_data = {
            "client_number": "TEST-2024-001",
            "client_type": "entreprise",
            "company_name": "Entreprise Test SA",
            "siret": "12345678901234",
            "email": "test@entreprise.fr",
            "phone": "0123456789",
            "address_line1": "1 rue de Test",
            "postal_code": "75001",
            "city": "Paris",
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/clients/", json=client_data)
        print(f"   ✅ Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   📄 Client créé: {data['client_number']} - {data['company_name']}")
            client_id = data['id']
            
            # Test 7 : Récupérer le client créé
            print("\n7️⃣  Test de récupération du client...")
            response = requests.get(f"{BASE_URL}/clients/{client_id}")
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 Client: {response.json()['company_name']}")
        elif response.status_code == 400:
            print(f"   ℹ️  Client déjà existant (normal si test déjà exécuté)")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("  ✅ Tests terminés !")
    print("=" * 70)
    print(f"\n📚 Documentation complète: {BASE_URL}/docs")


if __name__ == "__main__":
    print("\n⚠️  Assurez-vous que le serveur FastAPI est lancé (python main.py)\n")
    input("Appuyez sur Entrée pour continuer...")
    test_api()
