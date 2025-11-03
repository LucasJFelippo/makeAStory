import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { useParams, Link, useNavigate } from 'react-router-dom';
import "./ChatRoom.css";

const RENDER_URL = 'https://makeastory-backend.onrender.com';
const ROOM_URL = `${RENDER_URL}/r`;

function ChatRoom() {
    const { roomId } = useParams();
    const [socket, setSocket] = useState(null);
    const [status, setStatus] = useState('Connecting...');
    const [messages, setMessages] = useState([]);
    const [myMessage, setMyMessage] = useState('');
    const [users, setUsers] = useState([]);
    const [isAiThinking, setIsAiThinking] = useState(false);
    const [isGameStarted, setIsGameStarted] = useState(false);
    const chatEndRef = useRef(null);
    const navigate = useNavigate();

    // Rolar para o fim da página
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Roda UMA VEZ quando o componente carrega para configurar o chat
    useEffect(() => {
        const token = localStorage.getItem('token');

        if (!token) {
            setStatus("❌ Erro: Você não está logado.");
            navigate('/login');
            return;
        }

        // Conecta ao servidor Socket.IO
        const newSocket = io(ROOM_URL, {
            auth: {
                token: token
            }
        });

        // Quando a conexão é estabelecida com sucesso
        newSocket.on('connect', () => {
            newSocket.emit('join_room', { room_id: parseInt(roomId) }, (ack) => {
                if (ack && ack.status === 'ok') {
                    setStatus(`✔ Conectado à sala ${ack.room_id}`);
                    setUsers(ack.users_list || []);
                    setIsAiThinking(false);
                } else {
                    setStatus(ack ? `❌ ${ack.msg}` : 'Falha ao entrar (sem ack)');
                }
            });
        });

        // Servidor confirma a conexão (apenas log)
        newSocket.on('connect_ack', () => {
            setStatus(`✔ Conexão estabelecida`);
        });

        // Ouve por msgs do sistema
        newSocket.on('status_update', (data) => {
            const msg = { type: 'system', text: data.msg };
            setMessages((prev) => [...prev, msg]);
        });

        // Ouve pelo fim da rodada
        newSocket.on('round_ended', (data) => {
            setIsAiThinking(true);

            if (data && data.snippets) {
                // Mapeia os snippets de todos e adiciona ao chat
                const newMsgs = data.snippets.map(item => ({
                    type: 'snippet',
                    text: item.snippet,
                    sender: item.sender_username
                }));
                setMessages((prev) => [...prev, ...newMsgs]);
            }
        });

        // A IA terminou
        newSocket.on('new_story_part', (data) => {
            setIsAiThinking(false);

            const msg = {
                type: 'ai_response',
                story: data.text,
                image_url: data.image_url,
                song_url: data.music_url
            };
            setMessages((prev) => [...prev, msg]);
        });

        // Atualiza o drawer
        newSocket.on('user_list_update', (data) => {
            setUsers(data.users_list || []);
        });

        // Aviso de que um usuário enviou um snippet
        newSocket.on('snippet_received', (data) => {
            const msg = { type: 'system', text: `Recebido de: ${data.username}` };
            setMessages((prev) => [...prev, msg]);
        });

        // O jogo começou
        newSocket.on('game_started', (data) => {
            setIsGameStarted(true);
            const msg = { type: 'system', text: `🎮 Jogo iniciado por ${data.triggerer}` };
            setMessages((prev) => [...prev, msg]);
        });

        // Uma nova rodada começou
        newSocket.on('round_started', (data) => {
            setIsAiThinking(false);
            setIsGameStarted(true);
            const msg = { type: 'system', text: `🕒 Rodada ${data.round} iniciada` };
            setMessages((prev) => [...prev, msg]);
        });

        newSocket.on('connect_error', (err) => {
            setStatus(`❌ Erro de Conexão: ${err.message}`);
            if (err.message.includes('unauthorized')) {
                navigate('/login');
            }
        });

        // Salva o objeto do socket no estado do React
        setSocket(newSocket);

        return () => newSocket.disconnect();
    }, [roomId, navigate]);

    // --- Funções de Envio (Handlers) ---

    // Envia um snippet
    const handleSendMessage = (e) => {
        e.preventDefault();
        if (socket && myMessage) {
            socket.emit('story_snippet', { snippet: myMessage }, (ack) => {
                if (ack && ack.status === 'ok') {
                    setMyMessage('');
                } else {
                    const msg = { type: 'system', text: `❌ ${ack.msg}` };
                    setMessages((prev) => [...prev, msg]);
                }
            });
        }
    };

    // Envia o comando para iniciar o jogo
    const handleStartGame = () => {
        if (socket) {
            socket.emit('start_game', (ack) => {
                if (ack && ack.status === 'error') {
                    const msg = { type: 'system', text: `❌ ${ack.msg}` };
                    setMessages((prev) => [...prev, msg]);
                }
            });
        }
    };

    // --- Renderização ---

    const renderMessage = (msg, index) => {
        if (msg.type === 'ai_response') {
            return (
                <div key={index} className="ai-message">
                    <p>{msg.story}</p>

                    {msg.image_url &&
                        <img src={msg.image_url} alt="História gerada" style={{ maxWidth: '100%' }} />
                    }

                    {msg.song_url && (
                        <div className="audio-container">
                            <p className="audio-title">Música da Rodada:</p>
                            <audio controls src={msg.song_url} className="custom-audio-player">
                                Seu navegador não suporta a tag de áudio.
                            </audio>
                        </div>
                    )}
                </div>
            );
        }
        if (msg.type === 'system') {
            return <div key={index} className="system-message"><b>{msg.text}</b></div>;
        }
        return (
            <div key={index} className="user-message">
                <strong>{msg.sender || 'User'}:</strong> {msg.text}
            </div>
        );
    };

    // Estrutura visual da página
    return (
        <div className="chat-layout">
            <div className="drawer">
                <h3>Salas de Jogo</h3>
                <Link to="/rooms">{"< Voltar ao Lobby"}</Link>
                <div className="current-room-info">
                    Sala Atual:
                    <p>{roomId}</p>
                </div>
                <div className="user-list-container">
                    <h3>Usuários Conectados</h3>
                    <ul className="user-list">
                        {users.map((user, index) => (
                            <li key={index} className="user-list-item">
                                {user}
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
            <div className="chat-main">
                <div className="chat-header">
                    <h2>História da Sala {roomId}</h2>
                    <div className="status-bar">{status}</div>
                </div>
                <div className="message-list">
                    {messages.map(renderMessage)}
                    <div ref={chatEndRef} />
                </div>

                {isAiThinking && (
                    <div className="ai-thinking-indicator">
                        <div className="spinner"></div>
                        <span>IA está processando...</span>
                    </div>
                )}

                <div className="chat-actions">
                    <button onClick={handleStartGame} disabled={isGameStarted}>
                        Gerar História (IA)
                    </button>
                </div>
                <form onSubmit={handleSendMessage} className="message-input-form">
                    <input
                        type="text"
                        value={myMessage}
                        onChange={(e) => setMyMessage(e.target.value)}
                        placeholder="Digite sua parte da história..."
                    />
                    <button type="submit">Enviar</button>
                </form>
            </div>
        </div>
    );
}

export default ChatRoom;