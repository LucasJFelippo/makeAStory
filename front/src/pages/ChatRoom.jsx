import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { useParams, Link } from 'react-router-dom';
import "./ChatRoom.css";

const ROOM_URL = 'http://localhost:5000/r';

function ChatRoom() {
    const { roomId } = useParams();
    const [socket, setSocket] = useState(null);
    const [status, setStatus] = useState('Connecting...');
    const [messages, setMessages] = useState([]);
    const [myMessage, setMyMessage] = useState('');
    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        const newSocket = io(ROOM_URL); //
        newSocket.on('connect', () => {
            newSocket.emit('join_room', { room_id: parseInt(roomId) }, (ack) => {
                if (ack && ack.status === 'ok') {
                    setStatus(`✔ Joined room ${ack.room_id}`);
                } else {
                    setStatus(ack ? `❌ ${ack.msg}` : 'Joined (no ack)');
                }
            });
        });

        newSocket.on('connect_ack', () => {
            setStatus(`✔ Connection established`);
        });

        newSocket.on('snippet_broadcast', (data) => {
            if (data && data.snippets) {
                const newMsgs = data.snippets.map(item => ({
                    type: 'snippet',
                    text: item.snippet,
                    sender: item.sender.slice(0, 5) //
                }));
                setMessages((prev) => [...prev, ...newMsgs]);
            }
        });

        newSocket.on('game_started', (data) => {
            const msg = {
                type: 'system',
                text: `🎮 Game started by ${data.triggerer}`
            };
            setMessages((prev) => [...prev, msg]);
        });

        newSocket.on('round_started', (data) => {
            const msg = {
                type: 'system',
                text: `🕒 Round started by ${data.triggerer}`
            };
            setMessages((prev) => [...prev, msg]);
        });

        newSocket.on('ai_response', (data) => {
            const msg = { type: 'ai_response', ...data };
            setMessages((prev) => [...prev, msg]);
        });

        newSocket.on('connect_error', (err) => {
            setStatus(`❌ Connection Error: ${err.message}`);
        });

        setSocket(newSocket);

        return () => newSocket.disconnect();
    }, [roomId]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (socket && myMessage) {
            socket.emit('story_snippet', { snippet: myMessage, room: roomId }, (ack) => {

                if (ack && ack.status === 'ok') {
                    setMyMessage('');
                } else {
                    // Mostra erro se o servidor negar
                    const msg = { type: 'system', text: `${ack.msg}` };
                    setMessages((prev) => [...prev, msg]);
                }
            });
        }
    };

    const handleStartGame = () => {
        if (socket) {
            socket.emit('start_game', (ack) => {
                if (ack && ack.status === 'error') {
                    const msg = { type: 'system', text: `${ack.msg}` }; //
                    setMessages((prev) => [...prev, msg]);
                }
            });
        }
    };

    // Função de ajuda para renderizar diferentes tipos de msg
    const renderMessage = (msg, index) => {
        if (msg.type === 'ai_response') {
            return (
                <div key={index} className="ai-message">
                    <p>{msg.story}</p>
                    <img src={msg.image_url} alt="História gerada" />
                    <a href={msg.song_url} target="_blank" rel="noopener noreferrer">Ouvir música</a>
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

    return (
        <div className="chat-layout">
            {/* --- O Drawer (Menu Lateral) --- */}
            <div className="drawer">
                <h3>Salas de Jogo</h3>
                <Link to="/rooms">{"< Voltar ao Lobby"}</Link>

                <div className="current-room-info">
                    Sala Atual:
                    <p>{roomId}</p>
                </div>
            </div>

            {/* --- A Área Principal do Chat --- */}
            <div className="chat-main">
                {/* Cabeçalho do chat */}
                <div className="chat-header">
                    <h2>História da Sala {roomId}</h2>
                    <div className="status-bar">{status}</div>
                </div>

                {/* Lista de mensagens */}
                <div className="message-list">
                    {messages.map(renderMessage)}
                    <div ref={chatEndRef} />
                </div>
                {/* Botão de Ação */}
                <div className="chat-actions">
                    <button onClick={handleStartGame}>Gerar História (IA)</button>
                </div>

                {/* Input de nova mensagem */}
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