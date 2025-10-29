// front/src/App.jsx

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ChatRoom from './pages/ChatRoom';
import RoomSelector from './pages/RoomSelector';

// Não precisamos importar LoginPage ou RegisterPage por enquanto

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* A rota "/" (raiz) agora leva direto para o RoomSelector.
          É o nosso "ponto de entrada" temporário.
        */}
        <Route path="/" element={<RoomSelector />} />

        {/* Esta rota é redundante se "/" já é o seletor, 
          mas é bom manter para consistência.
        */}
        <Route path="/rooms" element={<RoomSelector />} />

        {/* Esta é a rota dinâmica para a sala de chat.
          O :roomId será pego pelo componente ChatRoom.
        */}
        <Route path="/chat/:roomId" element={<ChatRoom />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;