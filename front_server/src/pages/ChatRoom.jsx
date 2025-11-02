import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { useParams, Link, useNavigate } from 'react-router-dom';
import "./ChatRoom.css";

// A URL do namespace '/r'
const ROOM_URL = 'http://localhost:5000/r';

function ChatRoom() {
    const { roomId } = useParams(); // roomId agora é o ID numérico (ex: "0", "1")
    const [socket, setSocket] = useState(null);
    const [status, setStatus] = useState('Connecting...');
    const [messages, setMessages] = useState([]);
    const [myMessage, setMyMessage] = useState('');
    const [users, setUsers] = useState([]);
    const chatEndRef = useRef(null);
    const navigate = useNavigate();

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        // 1. AUTENTICAÇÃO: Pega o token do storage
        const token = localStorage.getItem('token');

        if (!token) {
            setStatus("❌ Erro: Você não está logado.");
            navigate('/login');
            return;
        }

        const newSocket = io(ROOM_URL, {
            auth: {
                token: token
            }
        });

        newSocket.on('connect', () => {
            newSocket.emit('join_room', { room_id: parseInt(roomId) }, (ack) => {
                if (ack && ack.status === 'ok') {
                    setStatus(`✔ Conectado à sala ${ack.room_id}`);
                    setUsers(ack.users_list || []);
                } else {
                    setStatus(ack ? `❌ ${ack.msg}` : 'Falha ao entrar (sem ack)');
                }
            });
        });

        // Ouve o 'connect_ack'
        newSocket.on('connect_ack', () => {
            setStatus(`✔ Conexão estabelecida`);
        });

        // 4. MUDANÇA DE EVENTO: Ouvir 'status_update'
        //
        newSocket.on('status_update', (data) => {
            const msg = { type: 'system', text: data.msg };
            setMessages((prev) => [...prev, msg]);
        });

        // 5. MUDANÇA DE EVENTO: 'snippet_broadcast' -> 'round_ended'
        //
        newSocket.on('round_ended', (data) => {
            if (data && data.snippets) {
                const newMsgs = data.snippets.map(item => ({
                    type: 'snippet',
                    text: item.snippet,
                    sender: item.sender_username // Back-end agora envia 'sender_username'
                }));
                setMessages((prev) => [...prev, ...newMsgs]);
            }
        });

        // 6. MUDANÇA DE EVENTO: 'ai_response' -> 'new_story_part' (É AQUI QUE A MÚSICA CHEGA!)
        //
        newSocket.on('new_story_part', (data) => {
            const msg = {
                type: 'ai_response',
                story: data.text, // Back-end envia 'text'
                image_url: data.image_url, // (ainda nulo, mas pronto)
                song_url: data.music_url // Back-end envia 'music_url'
            };
            setMessages((prev) => [...prev, msg]);
        });

        newSocket.on('user_list_update', (data) => {
            setUsers(data.users_list || []);
        });
        // 7. NOVO EVENTO: 'snippet_received'
        //
        newSocket.on('snippet_received', (data) => {
            const msg = { type: 'system', text: `Recebido de: ${data.username}` };
            setMessages((prev) => [...prev, msg]);
        });

        // 8. Ouve 'game_started' e 'round_started'
        newSocket.on('game_started', (data) => {
            const msg = { type: 'system', text: `🎮 Jogo iniciado por ${data.triggerer}` };
            setMessages((prev) => [...prev, msg]);
        });
        newSocket.on('round_started', (data) => {
            const msg = { type: 'system', text: `🕒 Rodada ${data.round} iniciada` };
            setMessages((prev) => [...prev, msg]);
        });

        newSocket.on('connect_error', (err) => {
            setStatus(`❌ Erro de Conexão: ${err.message}`);
            if (err.message.includes('unauthorized')) {
                navigate('/login');
            }
        });

        setSocket(newSocket);
        return () => newSocket.disconnect();
    }, [roomId, navigate]);

    // Envio de snippet (O 'ack' está correto pois room.py usa 'return')
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

    // Iniciar jogo (O 'ack' está correto pois room.py usa 'return' para erros)
    const handleStartGame = () => {
        if (socket) {
            socket.emit('start_game', (ack) => {
                if (ack && ack.status === 'error') {
                    const msg = { type: 'system', text: `❌ ${ack.msg}` };
                    setMessages((prev) => [...prev, msg]);
                }
                // Se der sucesso, o back-end não retorna ack,
                // mas emite 'game_started', o que é o ideal.
            });
        }
    };

    // Função de renderização ATUALIZADA para exibir a música
    const renderMessage = (msg, index) => {
        if (msg.type === 'ai_response') {
            return (
                <div key={index} className="ai-message" style={{ background: 'rgba(255, 0, 255, 0.2)', border: '1px solid #ff00ff' }}>
                    <p style={{ color: '#ffffff' }}>{msg.story}</p>

                    {msg.image_url &&
                        <img src={msg.image_url} alt="História gerada" style={{ maxWidth: '100%' }} />
                    }

                    {/* === AQUI ESTÁ A MÚSICA! === */}
                    {msg.song_url && (
                        <div>
                            <p style={{ margin: '10px 0 5px 0', fontWeight: 'bold' }}>Música da Rodada:</p>
                            <audio controls src={msg.song_url} style={{ width: '100%' }}>
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
        // (msg.type === 'snippet')
        return (
            <div key={index} className="user-message">
                <strong>{msg.sender || 'User'}:</strong> {msg.text}
            </div>
        );
    };

    // JSX (sem mudanças)
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
                <div className="chat-actions">
                    <button onClick={handleStartGame}>Gerar História (IA)</button>
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