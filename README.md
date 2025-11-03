# makeAStory

Lind da aplicação: https://makeastory-frontend.onrender.com

`makeAStory` é uma aplicação web de contação de histórias colaborativa e em tempo real. Este projeto foi desenvolvido como um estudo sobre arquiteturas de sistemas distribuídos, demonstrando um fluxo de dados complexo que integra uma aplicação React (front-end) com um back-end Python (Flask), WebSockets e múltiplas APIs de terceiros.

O fluxo principal do jogo é o seguinte:
1.  Usuários entram em um lobby e se juntam a uma sala de jogo.
2.  Cada jogador envia um pequeno fragmento de texto (um *snippet*) para continuar uma história.
3.  Quando todos enviam, o servidor back-end agrupa os snippets e os envia para a **API da OpenAI (GPT)**.
4.  A IA processa os textos e retorna uma narrativa coesa, unificando as ideias dos jogadores.
5.  O servidor, então, faz uma segunda chamada à IA para extrair tags de tema (gênero, emoção, instrumentos) da história gerada.
6.  Essas tags são usadas para consultar a **API da Jamendo**, que retorna uma trilha sonora instrumental que combina com o "clima" da história.
7.  O front-end recebe a história e a música, apresentando ambas aos jogadores, e uma nova rodada começa.

## Arquitetura do Sistema

O projeto é um monorepo que contém duas aplicações principais: `front_server` (o cliente) e `rest_server` (o servidor).

O servidor Flask opera de forma híbrida:

1.  **API REST (Stateless):** Usada para ações que não exigem tempo real.
    * `/auth/login`, `/auth/register`, `/auth/guest_login`: Gerencia a autenticação de usuários (registrados e convidados) e emite tokens JWT.
    * `/api/rooms`: Permite que usuários autenticados criem novas salas de jogo.

2.  **WebSocket (Stateful com Socket.IO):** Usado para toda a comunicação em tempo real.
    * **Namespace `/` (Lobby):** Envia a lista de salas ativas para os usuários no lobby.
    * **Namespace `/r` (Salas):** Gerencia a lógica de jogo, como entrada e saída de jogadores, recebimento de *snippets* e envio da história/música gerada pela IA.

### Front-end (`front_server`)

O front-end é uma **Single Page Application (SPA)** construída com React e Vite.

* **React Router:** Gerencia a navegação entre as telas de Login, Registro, Lobby e Sala de Jogo.
* **Axios:** Usado para fazer as chamadas REST para a API de autenticação e criação de salas.
* **Socket.io-client:** Gerencia a conexão WebSocket persistente com o servidor para o lobby e a lógica do jogo.

---

## Como Rodar Localmente

Para executar o projeto em um ambiente de desenvolvimento, você precisará rodar os dois servidores (back-end e front-end) em terminais separados.

O código configurado para rodar localmente (apontando para `localhost`) está disponível na branch `naoconseguiresolverconflito`:
* [https://github.com/lucasjfelippo/makeAStory/tree/naoconseguiresolverconflito](https://github.com/lucasjfelippo/makeAStory/tree/naoconseguiresolverconflito)

### Pré-requisitos
* Git
* Python 3.10+
* Node.js 18+ (ou a versão indicada no `package.json`)

### 1. Back-end (`rest_server`)

1.  **Navegue até a pasta do back-end:**
    ```bash
    cd makeAStory/rest_server
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente (CRÍTICO):**
    Este projeto **requer chaves de API** para funcionar. Você precisará solicitar as chaves aos autores do projeto.
    * `MAKEASTORY_GPT_API_KEY`: Chave da API da OpenAI.
    * `JAMENDO_CLIENT_ID`: Chave da API do Jamendo.
    * `MAKEASTORY_SOCKETIO_APP_KEY`: Uma string secreta aleatória (para o Flask).
    * `JWT_SECRET_KEY`: Outra string secreta aleatória (para o JWT).

    Configure-as no seu terminal:
    ```bash
    # Windows (PowerShell)
    $env:MAKEASTORY_GPT_API_KEY = "sk-..."
    # macOS/Linux
    export MAKEASTORY_GPT_API_KEY="sk-..."
    ```
    (Repita para todas as chaves)

5.  **Execute o servidor:**
    ```bash
    python run.py
    ```
    O back-end estará rodando em `http://localhost:5000`.

### 2. Front-end (`front_server`)

1.  **Abra um novo terminal.**

2.  **Navegue até a pasta do front-end:**
    ```bash
    cd makeAStory/front_server
    ```

3.  **Instale as dependências:**
    ```bash
    npm install
    ```

4.  **Execute o servidor de desenvolvimento:**
    ```bash
    npm run dev
    ```
   
    A aplicação estará acessível em `http://localhost:5173` (ou a porta indicada pelo Vite). Os arquivos nesta branch já estão configurados para se conectar ao back-end em `localhost:5000`.
