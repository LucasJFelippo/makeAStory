import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import './AuthForm.css'; // Reutiliza o mesmo CSS

const RENDER_URL = 'https://makeastory-frontend.onrender.com';
const REGISTER_URL = `${RENDER_URL}/auth/register`;

function RegisterPage() {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleRegister = async (e) => {
        e.preventDefault();
        setError('');

        try {
            //
            await axios.post(REGISTER_URL, {
                username: username,
                email: email,
                password: password
            });

            // Sucesso, redireciona para o login
            navigate('/login');

        } catch (err) {
            if (err.response) {
                // Erro do servidor (ex: "Username já existe")
                setError(err.response.data.msg);
            } else {
                setError('Não foi possível conectar ao servidor.');
            }
        }
    };

    return (
        <div className="auth-container">
            <form className="auth-form" onSubmit={handleRegister}>
                <h2>Registro</h2>
                {error && <p className="auth-error">{error}</p>}

                <div className="auth-form-group">
                    <label htmlFor="username">Usuário</label>
                    <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>

                <div className="auth-form-group">
                    <label htmlFor="email">Email</label>
                    <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>

                <div className="auth-form-group">
                    <label htmlFor="password">Senha</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>

                <button type="submit">Registrar</button>

                <div className="auth-form-link">
                    <p>Já tem uma conta? <Link to="/login">Faça login</Link></p>
                </div>
            </form>
        </div>
    );
}

export default RegisterPage;