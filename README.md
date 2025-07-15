# Partie 1 : Chatbot developpement with internet access - Documentation

For coherence with the code and the comments, I decided to write the documentation part in English.

## Overview

This application provides an intelligent search assistant that can either respond directly to user queries or perform web searches when needed. 
Plus, since I do not have enough VRAM GB, I decided to do an easier implementation of the VLM using the same API than the LLM. Thus, the chatbpot also includes image analysis  using vision-language models.

## What the Project Does

The main goal was to create a chatbot that can access the internet to find current information and use it in responses. 

The system I made choose wether to perform a search or not. Simple questions like "What is machine learning?" get direct answers, while questions about recent events trigger web searches.

## How It Works

### Smart Query Handling

At first, I coded my system such that the user query was directly used as it is to search on the web. However, the results were not that good, the websites obtained were far from being the most pertinent. Therefore, instead of using keywords to decide when to search, I let the AI itself make that decision. The `generate_search_query()` function in `app.py` sends each user question to the AI with special instructions from `query_generation_prompt` in `prompt.py` to either search the web or respond directly. This works better than rules because the AI understands context and can spot when current information is needed.

The AI returns a structured JSON response indicating either `{"search_web": "optimized query"}` or `{"direct_response": "complete answer"}`. I first had tried to create my own tools in a `available_tools` variable and use the `client.chat.completions.create()` function with  `tools=available_tools` and `tool_choice="auto"` as arguments but discovered the provider does not support the function calling. That's why I implemented the `search_web / direct_response` solution instead.


### Web Search Process

When search is needed, the `search_web()` function uses DuckDuckGo to find relevant pages. But instead of just using the search snippets, it calls `get_complete_page_content()` for each result to actually visit the page and read the full content. This gives much better information than just the preview text you see in search results.

The `get_complete_page_content()` function uses BeautifulSoup to clean up the web pages, removing ads and scripts but keeping all the readable text. Each page is limited to 10,000 characters to keep processing fast while still getting plenty of information. The `search_web()` function typically processes about 12 search results per query.

It may actually be pertinent to change this arbitrary values of 10000 and 12. For now, I just estimated that - worst case scenario- a token is worth 4 characters. Therefore, the 32768 tokens limit of my qwen model gives me the permission of around 130000 characters. Since I want to keep some tokens for the generation of the response and at the same time keep a big enough margin to avoid errors, I'm using 12*10000 = 120000 characters with the web_scraping.

A pertinent evolution would be to create a security which stops the current web scrapping when we reach a certain amount of tokens (for example 31900 to let tokens for the response) and start giving the response to the user. It would both allow to use all the possible tokens and reduce the risk of error.

### AI Integration

The `get_client()` function in `config.py` sets up the connection using the API key from the `.env` file. The main model is `qwen-2.5-coder-32b-instruct` which handles both deciding when to search and creating final responses. For the bonus image feature, the `analyze_image_with_vlm()` function uses `qwen2.5-vl-32b-instruct` which can analyze uploaded images.

Using OpenRouter makes it easy to switch models later if needed, and the free tier keeps costs at zero while testing and developing.

## Technical Setup

### Backend Structure

The Flask backend has four main files. The `app.py` file handles all the web requests and coordinates everything through the main `/api/chat` endpoint. The `config.py` file manages the API connection with the `get_client()` function. The `prompt.py` file contains `system_prompt` and `query_generation_prompt` that tell the AI how to behave. I took a very classic usually used instructions for the `system_prompt` but made `query_generation_prompt` on my own, explaning the choice between the 2 options and the exact JSON format to return. There is finally `vlm.py` which provides a standalone script for testing image analysis with the `analyze_image()` function.

The main `chat()` endpoint in `app.py` does the heavy lifting. It receives questions, calls `generate_search_query()` to decide whether to search, runs `search_web()` when needed, and returns answers with source information. Everything is designed to keep working even if individual parts fail.

### Search Implementation

The search process starts with the `generate_search_query()` function having the AI create better search terms based on what the user asked. Then `search_web()` uses DuckDuckGo to find relevant pages, and `get_complete_page_content()` visits each one to get the full content. This content gets combined with the original question and sent back to the AI in the final step of the `chat()` function to create a comprehensive answer.

This approach gives better responses because the AI has access to complete articles rather than just short summaries.

### Image Analysis

The bonus image feature lets users upload pictures through the `/api/analyze-image` endpoint and ask questions about them. The `analyze_image()` function in `app.py` handles file validation with `allowed_file()`, saves images temporarily with secure names, and calls `analyze_image_with_vlm()` to process them. Images are automatically deleted after processing. The vision model can describe images, read text in pictures, or answer specific questions about what it sees.



## Frontend Implementation

### React Application Structure

I built the frontend with React :
  ```bash
  npx create-react-app frontend
  cd frontend
  npm start
  ```
  
It has two main parts: `Chat.js` for chatting and `ImageUpload.js` for analyzing images. `App.js` switches between these two tabs when users click on them.

### Chat Interface

The `Chat.js` component talks to the backend using `/api/chat`. It saves all messages in React state. When users type and send messages, it shows typing dots while waiting for the AI response. If the AI searched the web, it shows the source links below the answer.

### Image Analysis Interface

The `ImageUpload.js` component lets users upload images to `/api/analyze-image`. It checks if the file is a valid image, shows a preview, and lets users ask custom questions about the image. After the AI analyzes it, the temporary file is deleted.

### API Integration and State Management

Both components use `fetch()` to call the backend APIs. They handle errors and show loading states. All data is stored with React's `useState` hooks. Chat messages are saved as a list, and image uploads track the selected file and results.

### Design and User Experience

The interface uses gradients and modern CSS effects. Users get instant feedback when they interact with the app. They can press Enter to send messages. The app clearly shows when answers come from web searches versus direct AI knowledge.


## Testing and Results

I tested the system with the provided example scenario and other similar questions. The `generate_search_query()` routing works correctly, identifying when web search is needed versus when direct answers are better. The source citations in the `chat()` response are accurate, and the system handles errors gracefully when websites are unavailable or searches fail.

## Error Handling

The system is built to keep working even when things go wrong. If `get_complete_page_content()` can't load a website, `search_web()` continues with other sources. If the AI's JSON response in `generate_search_query()` can't be parsed, it defaults to searching rather than failing. API errors are logged for debugging but don't break the user experience in the main `chat()` function.

## Security and Best Practices

API keys are stored in the `.env` file and loaded through `config.py` without ever being saved in the code repository. Uploaded images are handled securely in the `analyze_image()` function with `secure_filename()` sanitization and immediate cleanup after processing. The Flask app is configured with CORS properly for frontend integration while maintaining security.

## Performance Considerations

Web scraping in `get_complete_page_content()` is limited to prevent slow responses. Multiple search results are processed efficiently in the `search_web()` loop. Temporary files are cleaned up immediately in `analyze_image()` to prevent storage issues. The system is designed to be responsive even when processing multiple sources.


## Setup Requirements

The project needs Python with Flask for the web server, requests and BeautifulSoup for reading web pages, DuckDuckGo search integration, and the OpenAI client for connecting to the AI models.It allso requires an OpenRouter API key to use the AI models. The application runs on localhost:5000 in development mode.



# Partie 2 : Plan de déploiement Azure - Questions théoriques

N'ayant aucune expérience dans le domaine du déploiment, je précise que mes réponses dans cette partie sont théoriques. J'ai fait de mon mieux pour comprendre le fonctionnement général en me servant d'IAs ainsi que de guides et documentations cités à la fin.

## Architecture et Déploiement en Production

### Plan de déploiement Azure étape par étape

Le déploiement se fait en plusieurs phases bien distinctes. D'abord, on fait quelques manipulations pour préparer le code actuel:

- Il est utile de compiler les fichiers de src/ dans un nouveau dossier build/ créé automatiquement par React (npm run build). Le js devient illisible manuellement mais est beaucoup plus rapide à charger et à exécuter pour mettre en ligne.

```bash
cd frontend
npm run build
```

- On peut ensuite installer directement toutes les librairies nécessaires du repository en exécutant:

```bash
pip install -r requirements.txt
```

- **Modification importante** : Au lieu d'utiliser OpenRouter, on utilise Azure OpenAI Service pour héberger notre modèle LLM directement sur Azure pour améliorer la sécurité et la scabilité.

- Voilà donc un aperçu global de la structure du repository:
```
chatbot-project/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── config.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   ├── build/
│   └── package.json
│   └── package-lock.json
├── azure/
│   ├── app-service.json
│   └── static-web-app.json
├── .gitignore
└── README.md
```

On peut ensuite s'attaquer à l'environnement Azure en créant les ressources de base : un Resource Group, un Key Vault, les services d'hébergement, et le service Azure OpenAI. Le code à exécuter pour ka création ressemblerait à ça:

```bash
winget install Microsoft.AzureCLI  # par exemple sous Windows

az login
az account set --subscription "votre-subscription-id"

az group create --name rg-chatbot-prod --location "West Europe"

az keyvault create \
  --resource-group rg-chatbot-prod \
  --name kv-chatbot-secrets \
  --location "France Central" \
  --enable-rbac-authorization
```

### Création du service Azure OpenAI

Il faut donc ensuite ajouter la partie Azure OpenAI qui vient remplacer OpenRouter dans ce que j'ai fait sur l'exercice 1.

```bash
# Création du service Azure OpenAI
az cognitiveservices account create \
  --name chatbot-openai-service \
  --resource-group rg-chatbot-prod \
  --location "France Central" \
  --kind OpenAI \
  --sku S0

# Récupération de la clé API
az cognitiveservices account keys list \
  --name chatbot-openai-service \
  --resource-group rg-chatbot-prod

# Déploiement du modèle GPT-3.5-turbo
az cognitiveservices account deployment create \
  --name chatbot-openai-service \
  --resource-group rg-chatbot-prod \
  --deployment-name gpt-35-turbo \
  --model-name gpt-35-turbo \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"
```

Pour le backend, on utilise Azure App Service qui communique avec Azure OpenAI via les APIs natives.

```bash
az appservice plan create \
  --resource-group rg-chatbot-prod \
  --name asp-chatbot-backend \
  --location "West Europe" \
  --sku B1 \
  --is-linux

az webapp create \
  --resource-group rg-chatbot-prod \
  --plan asp-chatbot-backend \
  --name chatbot-backend-api \
  --runtime "PYTHON|3.11" \
  --deployment-local-git
```

Le frontend React va sur Azure Static Web Apps, qui s'intègre directement avec GitHub. Quand on pousse du code, Static Web Apps lance automatiquement `npm run build` et déploie la version optimisée. Il ne faut pas oublier de modifier *app.py* pour servir le dossier *build*.

```bash
az webapp create --resource-group rg-chatbot-prod --plan asp-chatbot-backend --name chatbot-backend-api --runtime "PYTHON|3.11"
```

### Prérequis COMPLETS

**Côté Azure :**
Pour déployer sur Azure, vous aurez d'abord besoin d'un abonnement Azure actif. Ensuite, il faut avoir au minimum le rôle "Contributor" sur votre subscription ou sur le Resource Group où vous voulez déployer. L'accès à Azure OpenAI nécessite une approbation spéciale car Microsoft maintient encore une liste d'attente pour ce service. Enfin, il faut s'assurer d'avoir un quota suffisant pour les services cognitifs, notamment pour les modèles de langage d'Azure.

**Côté développeur :**
Il faut tout d'abord ce dont j'ai eu besoin pour la création du chatbot : Node.js 16+ pour le build React, Python 3.11 installé localement pour tester ainsi que Git avec un accès push au repository GitHub. Il faut aussi le SDK Azure OpenAI pour Python (à la place de l'intégration API directe que j'ai faite). Enfin, il faut Azure CLI installé et configuré (`az login` fonctionnel).


**Côté organisation :**
Du point de vue organisationnel, il faudra d'abord faire valider les coûts estimés par votre hiérarchie avant le déploiement. Si on souhaite utiliser un domaine personnalisé plutôt que l'URL Azure par défaut, il faut obtenir les accès nécessaires pour modifier la configuration DNS de l'entreprise.


### Estimation des coûts mensuels 

Azure OpenAI Service va représenter la très grande majorité des coûts. Puis pour l'App Service, le plan B1 à 13€/mois pourrait suffire mais je pense que le S1 à 70€ est plus optimal car ajoute entre autres l'autoscaling et plus de possibilité de déployer des mises à jour sans interruption. Les services principaux sont alors:


- Azure OpenAI Service (GPT-3.5-turbo) : ~100-200€/mois selon l'usage
  - Prix : ~0.0015€ pour 1000 tokens d'input, ~0.002€ pour 1000 tokens d'output
  - Estimation : 50k requêtes/mois = ~150€
- App Service Plan S1 : 70€/mois
- Static Web Apps : gratuit jusqu'à 100GB de bande passante
- Key Vault : 0.50€/mois pour les opérations de base
- Application Insights : 5€/mois (5GB de données inclus)
- Transfert réseau : environ quelques € par mois

Cela représente donc un total de 180€ à 280€ par mois.

Pour économiser, on peut :
- Utiliser GPT-3.5 au lieu de GPT-4 car 3x moins cher (déjà fait dans l'estimation)
- Implémenter un cache Redis pour les réponses fréquentes
- Optimiser la longueur des prompts et réponses

### Architecture scalable proposée

Au début, l'architecture reste assez simple. Les utilisateurs accèdent au site hébergé sur Static Web Apps, qui communique avec notre App Service backend, lequel appelle ensuite notre cluster GPU pour le modèle LLM. En parallèle, l'App Service fait aussi ses recherches DuckDuckGo.

```
Users → Static Web Apps → App Service → Azure OpenAI Service
                              ↓
                    DuckDuckGo Search API
```

Quand le trafic augmente, on peut étoffer le système. On ajoute Azure Front Door devant tout pour gérer la charge globale et améliorer les performances. Un cache Redis devient quasi-obligatoire parce que les appels GPU coûtent cher - autant éviter de refaire les mêmes calculs. Une base SQL peut stocker l'historique des conversations si on veut ajouter des fonctionnalités comme la mémoire conversationnelle.

```
Users → Azure Front Door → Static Web Apps → App Service → Azure OpenAI
                              ↓                    ↓
                    Application Gateway      Azure Cache for Redis
                              ↓                    ↓
                         Azure SQL DB       Application Insights
```

Pour vraiment scaler, on pourrait peut-être utiliser Kubernetes avec plusieurs replicas du modèle. Le problème est que chaque instance GPU coûte cher, donc il faut vraiment optimiser l'utilisation. On peut aussi implémenter de l'auto-scaling intelligent qui lance des instances supplémentaires seulement pendant les pics de charge.
L'idée étant de commencer simple et d'ajouter de la complexité seulement quand c'est nécessaire. Avec les coûts GPU, mieux vaut avoir un système qui marche bien à petite échelle avant de voir plus grand.

### Points d'attention cruciaux

**Accès nécessaires :**
Il faut vraiment faire attention aux permissions. "Contributor" sur le Resource Group suffit pour la plupart des services, mais Azure OpenAI nécessite une approbation spéciale de Microsoft.

**Permissions spécifiques :**
- Cognitive Services Contributor (pour gérer Azure OpenAI)
- Créer des App Services et Static Web Apps
- Accès en écriture au Key Vault (ou au moins Key Vault Secrets User)
- Pouvoir assigner des rôles pour l'identité managée
- Accès aux logs Application Insights

**Autres accès organisationnels :**
- **Demande d'accès Azure OpenAI** (il faut remplir un formulaire Microsoft donc un délai est possible)
- Admin sur le repository GitHub pour configurer les secrets de déploiement
- Accès aux DNS si domaine personnalisé
- Coordination avec l'équipe sécurité pour valider l'architecture

### Services Azure utilisés et justifications

**Azure OpenAI Service** : Managé par Microsoft, pas d'infrastructure à gérer, modèles pré-entraînés (GPT-3.5, GPT-4), facturation transparente à l'usage, SLA enterprise, conformité RGPD native.

**App Service** plutôt que des VMs car c'est managé, avec auto-scaling, et ça gère Python nativement. Plus simple que des containers pour ce cas d'usage.

**Static Web Apps** au lieu d'un storage + CDN classique car l'intégration GitHub est automatique et ça inclut déjà HTTPS + CDN.

**Key Vault** obligatoire pour la sécurité - jamais de secrets en dur dans le code.

**Application Insights** pour le monitoring temps réel et les alertes. Essentiel pour surveiller les coûts Azure OpenAI en temps réel.

### Considérations de sécurité

L'avantage majeur est que les données ne quittent jamais l'environnement Azure. La conformité RGPD facilitée et il n'y a pas de transfert vers des services tiers.

De plus, tout passe en HTTPS obligatoirement. Les clés Azure OpenAI sont dans Key Vault avec des permissions granulaires. L'identité managée évite de stocker des credentials.

CORS configuré précisément pour autoriser seulement les domaines légitimes. Network isolation possible avec Private Endpoints pour Azure OpenAI.

Les logs Application Insights ne doivent pas contenir d'informations sensibles (attention aux prompts utilisateur).

### Gestion des secrets et API keys

Les clés Azure OpenAI vont dans Key Vault, et l'App Service y accède via son identité managée. Le code change légèrement :

```python

from openai import AzureOpenAI
import os

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Exemple d'appel
response = client.chat.completions.create(
    model="gpt-35-turbo",  # Nom du déploiement
    messages=[{"role": "user", "content": context}],
    max_tokens=500,
    temperature=0.7
)
```

Pour les déploiements, GitHub Actions utilise un service principal avec juste les permissions nécessaires.

## Stratégie de mise en production

### CI/CD Pipeline

Le pipeline doit gérer l'intégration avec Azure OpenAI :

1. Tests du code application
2. **Tests d'intégration avec Azure OpenAI** (appels API)
3. Build frontend React  
4. Déploiement App Service
5. Tests de bout en bout sur l'environnement de staging
6. **Monitoring des coûts Azure OpenAI** post-déploiement

L'avantage, c'est qu'on peut facilement ajouter des environnements de staging avec des déploiements Azure OpenAI séparés.

### Monitoring et logs

Application Insights collecte automatiquement les métriques de base : temps de réponse, erreurs HTTP, usage CPU/mémoire.

**Métriques spécifiques Azure OpenAI à surveiller :**
- Latence des appels au modèle
- Nombre de tokens consommés (impact direct sur les coûts)
- Taux d'erreur des APIs Azure OpenAI  
- Quotas et limites de débit
- Coûts en temps réel


### Gestion des erreurs

L'App Service redémarre automatiquement en cas de crash. Mais il faut prévoir les cas spécifiques Azure OpenAI :

- Service Azure OpenAI indisponible → fallback sur message d'erreur gracieux
- Quota de tokens dépassé → file d'attente ou limitation de débit côté application
- Rate limiting → retry automatique avec backoff exponentiel
- Région Azure indisponible → basculement sur une autre région (si configuré)

Le frontend doit gérer gracieusement les timeouts et afficher des messages d'erreur clairs.

### Stratégie de backup

Le code source est dans Git, donc déjà sauvegardé. Les configurations Azure peuvent être exportées en ARM templates pour recréer l'infrastructure rapidement.

**Spécifique Azure OpenAI :**
- Configuration des déploiements de modèles sauvegardée
- Historique des conversations (si stocké) dans Azure SQL avec backup automatique
- Métriques d'usage et coûts exportés régulièrement pour analyse

Les secrets Key Vault sont répliqués automatiquement dans la région.

L'architecture Azure OpenAI permet de garder toutes les données dans l'écosystème Microsoft, avec une sécurité enterprise et une scalabilité native, tout en restant sur des coûts raisonnables comparé à une infrastructure GPU custom.

## Sources

1. **Microsoft Azure Documentation**  
   https://learn.microsoft.com/en-us/azure/  
   *Documentation officielle complète des services Azure*

2. **Deployment - Create React App**  
   https://create-react-app.dev/docs/deployment/  
   *Documentation officielle pour le déploiement d'applications React*

3. **Deploying Azure OpenAI in Production: A Comprehensive Guide**  
   https://medium.com/@kyeg/deploying-azure-openai-in-production-a-comprehensive-guide-a521d0c4da8a  
   *Guide pratique pour le déploiement Azure OpenAI en environnement de production*

4. **Deploying Python to Azure App Service - GitHub Docs**  
   https://docs.github.com/en/actions/how-tos/managing-workflow-runs-and-deployments/deploying-to-third-party-platforms/deploying-python-to-azure-app-service  
   *Documentation GitHub pour le déploiement d'applications Python sur App Service*

5. **How to Handle Secrets with Azure Key Vault**  
   https://blog.gitguardian.com/how-to-handle-secrets-with-azure-key-vault/  
   *Guide pratique pour la gestion sécurisée des secrets avec Azure Key Vault*

6. **Azure Cost Calculator: Estimating Azure Costs, Step by Step**  
   https://spot.io/resources/azure-cost-optimization/azure-cost-calculator-estimating-azure-costs-step-by-step/  
   *Guide détaillé pour l'estimation et l'optimisation des coûts Azure*

7. **The Complete Guide To The Azure Pricing Calculator**  
   https://www.synextra.co.uk/knowledge-base/the-azure-pricing-calculator/  
   *Guide complet d'utilisation du calculateur de prix Azure*

8. **CI/CD with GitHub Actions on Azure Web App (Dev, QA and Prod)**  
   https://medium.com/@lorenzouriel/ci-cd-with-github-actions-on-azure-web-app-dev-qa-and-prod-241c1cadd9b6  
   *Guide complet pour créer un pipeline CI/CD multi-environnements avec GitHub Actions*

9. **Building a CI/CD pipeline for your Azure project with GitHub Actions from scratch**  
   https://dev.to/manuelsidler/building-a-ci-cd-pipeline-for-your-azure-project-with-github-actions-from-scratch-48cb  
   *Construction complète d'un pipeline CI/CD Azure depuis zéro avec ARM templates*


# Partie 3 : Vision Language Models

Comme mentionné dans la partie 1, n'ayant pas suffisament de VRAM, j'ai réalisé une solution bien plus simple, ne nécessitant pas l'utilisation du VLM en local.

Puis, pour ce qui est de la question théorique, j'ai surtout essayé de comprendre en quoi consiste une vectorisation incluant des VLM et surtout quels sont les enjeux qui y sont associés, ce que je résumerais de la sorte:

Les systèmes de vectorisation de documents avec VLMs permettent de traiter des documents complets qui contiennent à la fois du texte et des images, plutôt que juste le texte comme les systèmes classiques. L'idée c'est que quand on a un rapport avec des graphiques et des schémas, il faut que le système lise et comprenne aussi bien le texte que les visuels (sinon il perd la moitié des informations). Le principal enjeu est de garder le lien entre les éléments qui vont ensemble. 

L'autre gros problème c'est le coût et la performance. Analyser des images avec des VLMs est beaucoup plus lent et cher que traiter du texte, donc il faut optimiser pour éviter que ça devienne trop lourd. Et puis il faut s'assurer que l'extraction des données visuelles soit précise, surtout pour des graphiques avec des chiffres importants.

Une des approches qui est souvent mentionnée est la création de "chunks hybrides" où on garde ensemble le texte et les images qui se référencent mutuellement. Certains systèmes utilisent aussi des métadonnées pour créer des liens entre segments, comme des pointeurs qui disent associent un graphique à un paragraphe.
