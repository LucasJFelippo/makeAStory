import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ChatRoom from './pages/ChatRoom';
import RoomSelector from './pages/RoomSelector';
import LoginPage from './pages/LoginPage'; 
import RegisterPage from './pages/RegisterPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Define a página de login como a rota principal */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* As rotas do jogo (proteja-as depois, se quiser) */}
        <Route path="/rooms" element={<RoomSelector />} />
        <Route path="/chat/:roomId" element={<ChatRoom />} />

        {/* Rota inicial agora é o login */}
        <Route path="/" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;