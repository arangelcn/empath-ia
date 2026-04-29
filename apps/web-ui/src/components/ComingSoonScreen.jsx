import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Brain, ArrowLeft, Github, Heart } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function NeuralCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const NODE_COUNT = 40;
    const nodes = Array.from({ length: NODE_COUNT }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 2 + 1,
      pulse: Math.random() * Math.PI * 2,
    }));

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      nodes.forEach(n => {
        n.x += n.vx;
        n.y += n.vy;
        n.pulse += 0.02;
        if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
        if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
      });

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 130) {
            const alpha = (1 - dist / 130) * 0.2;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = `rgba(74,217,217,${alpha})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }

      nodes.forEach(n => {
        const glow = Math.sin(n.pulse) * 0.5 + 0.5;
        const grad = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 3);
        grad.addColorStop(0, `rgba(74,144,226,${0.7 + glow * 0.3})`);
        grad.addColorStop(1, 'rgba(74,144,226,0)');
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r * (1 + glow * 0.4), 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
      });

      animId = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full opacity-50 pointer-events-none"
    />
  );
}

const features = [
  { label: 'IA Conversacional', done: true },
  { label: 'Análise Emocional', done: true },
  { label: 'Voz Neural', done: true },
  { label: 'Painel do Terapeuta', done: true },
  { label: 'Ajustes de segurança', done: false },
  { label: 'Testes de estabilidade', done: false },
];

export default function ComingSoonScreen() {
  const navigate = useNavigate();

  return (
    <div
      className="min-h-screen text-white font-sans flex flex-col items-center justify-center relative overflow-hidden"
      style={{ backgroundColor: '#1A2B4C' }}
    >
      {/* Fundo animado */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <NeuralCanvas />
        {/* Orbs */}
        {[
          { size: 500, left: '-10%', top: '0%', color: 'rgba(74,144,226,0.10)' },
          { size: 350, left: '70%', top: '10%', color: 'rgba(178,141,255,0.08)' },
          { size: 300, left: '40%', top: '60%', color: 'rgba(110,210,232,0.07)' },
        ].map((orb, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full blur-3xl pointer-events-none"
            style={{
              width: orb.size,
              height: orb.size,
              left: orb.left,
              top: orb.top,
              background: orb.color,
            }}
            animate={{ y: [0, -20, 0], scale: [1, 1.04, 1] }}
            transition={{ duration: 9 + i * 2, repeat: Infinity, ease: 'easeInOut' }}
          />
        ))}
      </div>

      {/* Conteúdo principal */}
      <div className="relative z-10 flex flex-col items-center text-center px-6 max-w-2xl w-full">

        {/* Logo */}
        <motion.div
          className="flex items-center gap-2.5 mb-12"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <motion.div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #4A90E2, #6ED2E8)' }}
            animate={{
              boxShadow: [
                '0 0 15px rgba(74,144,226,0.3)',
                '0 0 30px rgba(74,144,226,0.55)',
                '0 0 15px rgba(74,144,226,0.3)',
              ],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Brain size={20} className="text-white" />
          </motion.div>
          <span className="text-2xl font-bold tracking-tight">
            Empat<span style={{ color: '#6ED2E8' }}>.IA</span>
          </span>
        </motion.div>

        {/* Ícone central animado */}
        <motion.div
          className="relative mb-8"
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.7, type: 'spring', stiffness: 120 }}
        >
          <motion.div
            className="w-24 h-24 rounded-3xl flex items-center justify-center mx-auto"
            style={{
              background: 'linear-gradient(135deg, #4A90E2 0%, #6ED2E8 50%, #B28DFF 100%)',
              boxShadow: '0 0 50px rgba(74,144,226,0.4)',
            }}
            animate={{ rotate: [0, 4, -4, 0] }}
            transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
          >
            <Heart size={42} className="text-white" />
          </motion.div>

          {/* Ping ao redor */}
          <motion.div
            className="absolute inset-0 rounded-3xl"
            style={{ border: '2px solid rgba(74,144,226,0.3)' }}
            animate={{ scale: [1, 1.25, 1], opacity: [0.6, 0, 0.6] }}
            transition={{ duration: 2.5, repeat: Infinity }}
          />
        </motion.div>

        {/* Título */}
        <motion.h1
          className="text-4xl md:text-5xl font-bold leading-tight mb-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15 }}
        >
          Trabalho em{' '}
          <span
            style={{
              background: 'linear-gradient(135deg, #4AD9D9 0%, #6ED2E8 50%, #B28DFF 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            progresso
          </span>
        </motion.h1>

        {/* Subtítulo */}
        <motion.p
          className="text-xl md:text-2xl font-medium text-slate-300 mb-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.25 }}
        >
          Estamos quase lá
        </motion.p>

        <motion.p
          className="text-slate-400 text-base leading-relaxed mb-10 max-w-md"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.35 }}
        >
          A plataforma está sendo preparada para oferecer a melhor experiência possível.
          Em breve estará disponível para todos.
        </motion.p>

        {/* Checklist de funcionalidades */}
        <motion.div
          className="w-full max-w-sm mb-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.45 }}
        >
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 text-left">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-4">
              Status do projeto
            </p>
            <ul className="space-y-3">
              {features.map((f, i) => (
                <motion.li
                  key={f.label}
                  className="flex items-center gap-3 text-sm"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.07 }}
                >
                  <span
                    className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold"
                    style={
                      f.done
                        ? { background: 'rgba(74,217,217,0.2)', color: '#4AD9D9', border: '1px solid rgba(74,217,217,0.4)' }
                        : { background: 'rgba(255,255,255,0.06)', color: '#64748b', border: '1px solid rgba(255,255,255,0.1)' }
                    }
                  >
                    {f.done ? '✓' : '·'}
                  </span>
                  <span className={f.done ? 'text-slate-300' : 'text-slate-500'}>
                    {f.label}
                  </span>
                </motion.li>
              ))}
            </ul>
          </div>
        </motion.div>

        {/* Botões */}
        <motion.div
          className="flex flex-col sm:flex-row items-center gap-3 w-full max-w-sm"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.9 }}
        >
          <motion.button
            onClick={() => navigate('/')}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-white/15 px-5 py-2.5 text-sm font-semibold text-slate-300 transition-all hover:border-white/30 hover:bg-white/5 hover:text-white"
            whileHover={{ y: -1 }}
            whileTap={{ y: 0 }}
          >
            <ArrowLeft size={15} />
            Voltar ao início
          </motion.button>

          <motion.a
            href="https://github.com/arangelcn/empath-ia"
            target="_blank"
            rel="noopener noreferrer"
            className="flex w-full items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white shadow-sm"
            style={{ background: 'linear-gradient(135deg, #4A90E2, #6ED2E8)' }}
            whileHover={{ y: -1, boxShadow: '0 8px 22px rgba(74,144,226,0.28)' }}
            whileTap={{ y: 0 }}
          >
            <Github size={15} />
            Ver no GitHub
          </motion.a>
        </motion.div>

        {/* Rodapé */}
        <motion.p
          className="mt-12 text-xs text-slate-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.1 }}
        >
          © {new Date().getFullYear()} Empat.IA · Inteligência artificial a serviço do bem-estar humano
        </motion.p>
      </div>
    </div>
  );
}
