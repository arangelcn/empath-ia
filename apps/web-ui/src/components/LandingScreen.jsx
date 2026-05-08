import React, { useEffect, useRef, useState } from 'react';
import { motion, useInView, useAnimation, AnimatePresence } from 'framer-motion';
import {
  Brain, Heart, Shield, Zap, Mic, Eye, ArrowRight,
  ChevronDown, Mail, Phone, MessageCircle, Users,
  Sparkles, Lock, Activity, RefreshCw
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

/* --------------------------------------------------------------------------
   Neural Network Canvas Animation
   -------------------------------------------------------------------------- */
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

    const NODE_COUNT = 60;
    const nodes = Array.from({ length: NODE_COUNT }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 2.5 + 1,
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
          if (dist < 120) {
            const alpha = (1 - dist / 120) * 0.25;
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
        grad.addColorStop(0, `rgba(74,144,226,${0.8 + glow * 0.2})`);
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
      className="absolute inset-0 w-full h-full opacity-60 pointer-events-none"
    />
  );
}

/* --------------------------------------------------------------------------
   Floating Orbs
   -------------------------------------------------------------------------- */
function FloatingOrbs() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {[
        { size: 400, x: '-10%', y: '5%', color: 'rgba(74,144,226,0.12)', delay: 0 },
        { size: 300, x: '75%', y: '20%', color: 'rgba(110,210,232,0.10)', delay: 2 },
        { size: 350, x: '30%', y: '60%', color: 'rgba(178,141,255,0.09)', delay: 4 },
        { size: 250, x: '85%', y: '70%', color: 'rgba(74,217,217,0.08)', delay: 1 },
      ].map((orb, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full blur-3xl"
          style={{
            width: orb.size,
            height: orb.size,
            left: orb.x,
            top: orb.y,
            background: orb.color,
          }}
          animate={{
            y: [0, -30, 0],
            scale: [1, 1.05, 1],
          }}
          transition={{
            duration: 8 + i * 2,
            delay: orb.delay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  );
}

/* --------------------------------------------------------------------------
   Section wrapper with scroll animation
   -------------------------------------------------------------------------- */
function RevealSection({ children, className = '', delay = 0 }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, delay, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}

/* --------------------------------------------------------------------------
   Feature Card
   -------------------------------------------------------------------------- */
function FeatureCard({ icon: Icon, title, description, color, delay }) {
  const [hovered, setHovered] = useState(false);
  return (
    <RevealSection delay={delay}>
      <motion.div
        className="relative p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden group cursor-default"
        whileHover={{ y: -2 }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
        onHoverStart={() => setHovered(true)}
        onHoverEnd={() => setHovered(false)}
      >
        <motion.div
          className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
          style={{ background: `radial-gradient(circle at 50% 0%, ${color}18 0%, transparent 70%)` }}
        />
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
          style={{ background: `${color}20`, border: `1px solid ${color}40` }}
        >
          <Icon size={22} style={{ color }} />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2 font-heading">{title}</h3>
        <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
        <motion.div
          className="absolute bottom-0 left-0 h-0.5 rounded-full"
          style={{ background: `linear-gradient(90deg, ${color}, transparent)` }}
          initial={{ width: '0%' }}
          animate={hovered ? { width: '100%' } : { width: '0%' }}
          transition={{ duration: 0.4 }}
        />
      </motion.div>
    </RevealSection>
  );
}

/* --------------------------------------------------------------------------
   Step Card (How it works)
   -------------------------------------------------------------------------- */
function StepCard({ number, title, description, delay }) {
  return (
    <RevealSection delay={delay}>
      <div className="relative flex gap-5">
        <div className="flex-shrink-0 flex flex-col items-center">
          <motion.div
            className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold font-heading"
            style={{
              background: 'linear-gradient(135deg, #4A90E2, #6ED2E8)',
              boxShadow: '0 0 20px rgba(74,144,226,0.4)',
            }}
            whileHover={{ y: -1 }}
          >
            {number}
          </motion.div>
          {number < 4 && <div className="w-px flex-1 mt-2 bg-gradient-to-b from-primary-500/50 to-transparent" />}
        </div>
        <div className="pb-8">
          <h3 className="text-lg font-semibold text-white mb-1 font-heading">{title}</h3>
          <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
        </div>
      </div>
    </RevealSection>
  );
}

/* --------------------------------------------------------------------------
   Stat Badge
   -------------------------------------------------------------------------- */
function StatBadge({ value, label, color }) {
  return (
    <div className="text-center">
      <div className="text-3xl md:text-4xl font-bold font-heading" style={{ color }}>
        {value}
      </div>
      <div className="text-xs text-slate-400 mt-1 uppercase tracking-wider">{label}</div>
    </div>
  );
}

/* --------------------------------------------------------------------------
   Main LandingScreen
   -------------------------------------------------------------------------- */
export default function LandingScreen() {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToSection = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen text-white font-sans overflow-x-hidden" style={{ backgroundColor: '#1A2B4C' }}>

      {/* ── FUNDO FIXO (cobre toda a página ao rolar) ── */}
      <div className="fixed inset-0 z-0 pointer-events-none" style={{ backgroundColor: '#1A2B4C' }}>
        <FloatingOrbs />
        <NeuralCanvas />
      </div>

      {/* ── NAV ─────────────────────────────────────────────────── */}
      <motion.nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrolled ? 'bg-background-dark/80 backdrop-blur-xl border-b border-white/10' : ''
        }`}
        initial={{ y: -60, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <motion.div
              className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #4A90E2, #6ED2E8)' }}
              animate={{ boxShadow: ['0 0 15px rgba(74,144,226,0.3)', '0 0 25px rgba(74,144,226,0.5)', '0 0 15px rgba(74,144,226,0.3)'] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Brain size={18} className="text-white" />
            </motion.div>
            <span className="text-xl font-bold font-heading tracking-tight">
              Empat<span className="text-primary-400">.IA</span>
            </span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-sm text-slate-400">
            {['features', 'como-funciona', 'contato'].map(id => (
              <button
                key={id}
                onClick={() => scrollToSection(id)}
                className="hover:text-white transition-colors capitalize"
              >
                {id === 'como-funciona' ? 'Como funciona' : id.charAt(0).toUpperCase() + id.slice(1)}
              </button>
            ))}
          </div>
          <motion.button
            onClick={() => navigate('/login')}
            className="rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-sm"
            style={{ background: 'linear-gradient(135deg, #4A90E2, #6ED2E8)' }}
            whileHover={{ y: -1, boxShadow: '0 8px 22px rgba(74,144,226,0.28)' }}
            whileTap={{ y: 0 }}
          >
            Entrar
          </motion.button>
        </div>
      </motion.nav>

      {/* ── SECÇÃO 1 · PROPÓSITO ────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 pt-20 overflow-hidden">

        <div className="relative z-10 text-center max-w-4xl mx-auto">

          {/* Eyebrow */}
          <motion.div
            className="relative inline-block mb-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <motion.div
              className="absolute left-0 top-1/2 -translate-y-1/2 h-px w-8 md:w-16"
              style={{ background: 'linear-gradient(90deg, transparent, #4AD9D9)' }}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.8, delay: 0.5 }}
            />
            <motion.div
              className="absolute right-0 top-1/2 -translate-y-1/2 h-px w-8 md:w-16"
              style={{ background: 'linear-gradient(90deg, #4AD9D9, transparent)' }}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.8, delay: 0.5 }}
            />
            <span className="px-10 md:px-20 text-xs font-semibold uppercase tracking-[0.3em] text-therapy-trust/80">
              Nossa razão de existir
            </span>
          </motion.div>

          {/* Frase principal */}
          <motion.h1
            className="text-3xl md:text-4xl lg:text-5xl font-bold font-heading leading-snug mb-5"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.3 }}
          >
            <span className="text-white">A Empat.IA existe para </span>
            <span
              style={{
                background: 'linear-gradient(135deg, #4AD9D9 0%, #6ED2E8 50%, #B28DFF 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              potencializar
            </span>
            <span className="text-white"> o trabalho terapêutico —</span>
            <br />
            <span className="text-slate-200 font-medium text-2xl md:text-3xl lg:text-4xl">
              não substituir o terapeuta,{' '}
              <span className="text-white font-bold">mas ampliar o seu alcance.</span>
            </span>
          </motion.h1>

          {/* Subtexto */}
          <motion.p
            className="text-slate-400 text-base md:text-lg max-w-2xl mx-auto leading-relaxed mb-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.5 }}
          >
            O humano continua no centro.
            A IA oferece continuidade, escuta ativa e suporte entre sessões —
            para que o vínculo terapêutico seja ainda mais profundo.
          </motion.p>

          {/* Tags */}
          <motion.div
            className="flex flex-wrap items-center justify-center gap-3"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.65 }}
          >
            {[
              { label: 'IA como aliada',       color: '#4A90E2', icon: '🤝' },
              { label: 'Terapeuta no centro',   color: '#6ED2E8', icon: '🧠' },
              { label: 'Continuidade real',     color: '#B28DFF', icon: '🔄' },
              { label: 'Sem substituição',      color: '#4AD9D9', icon: '❤️' },
            ].map((tag) => (
              <span
                key={tag.label}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold border"
                style={{
                  borderColor: `${tag.color}40`,
                  background: `${tag.color}12`,
                  color: tag.color,
                }}
              >
                <span>{tag.icon}</span>
                {tag.label}
              </span>
            ))}
          </motion.div>
        </div>

        {/* Scroll hint → secção 2 */}
        <motion.button
          onClick={() => scrollToSection('hero')}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-slate-500 hover:text-slate-300 transition-colors"
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <ChevronDown size={24} />
        </motion.button>
      </section>

      {/* ── SECÇÃO 2 · HERO ─────────────────────────────────────── */}
      <section id="hero" className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
        {/* Orb central suave de fundo */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 70% 60% at 50% 50%, rgba(74,144,226,0.07) 0%, transparent 70%)' }}
        />

        <div className="relative z-10 text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, type: 'spring', stiffness: 120 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-primary-500/30 bg-primary-500/10 text-primary-300 text-sm font-medium mb-8"
          >
            <Sparkles size={14} />
            Terapia Virtual com Inteligência Artificial
          </motion.div>

          <motion.h2
            className="text-5xl md:text-7xl font-bold font-heading leading-none mb-6"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.1 }}
          >
            <span className="text-white">
              Saúde mental
            </span>
            <br />
            <span className="bg-gradient-to-r from-primary-400 via-secondary-400 to-accent-400 bg-clip-text text-transparent">
              reimaginada
            </span>
          </motion.h2>

          <motion.p
            className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            Uma plataforma terapêutica virtual que combina IA avançada, análise emocional
            em tempo real e continuidade entre sessões para uma jornada de bem-estar
            verdadeiramente personalizada.
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.3 }}
          >
            <motion.button
              onClick={() => navigate('/login')}
              className="rounded-xl px-7 py-3.5 text-base font-semibold text-white shadow-sm"
              style={{ background: 'linear-gradient(135deg, #4A90E2 0%, #6ED2E8 50%, #B28DFF 100%)' }}
              whileHover={{ y: -1, boxShadow: '0 12px 30px rgba(74,144,226,0.28)' }}
              whileTap={{ y: 0 }}
            >
              <span className="flex items-center gap-2">
                Ir para o App
                <motion.span
                  animate={{ x: [0, 4, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  <ArrowRight size={18} />
                </motion.span>
              </span>
            </motion.button>

            <motion.button
              onClick={() => scrollToSection('features')}
              className="rounded-xl border border-white/15 px-7 py-3.5 text-base font-semibold text-slate-300 transition-all hover:border-white/30 hover:bg-white/5 hover:text-white"
              whileHover={{ y: -1 }}
              whileTap={{ y: 0 }}
            >
              Saiba mais
            </motion.button>
          </motion.div>

          {/* Stats */}
          <motion.div
            className="w-full max-w-lg mx-auto grid grid-cols-3 gap-6"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            {[
              { value: 'GPT-4', label: 'IA de ponta',  color: '#4A90E2' },
              { value: '100%',  label: 'Privacidade',   color: '#6ED2E8' },
              { value: '24/7',  label: 'Disponível',    color: '#B28DFF' },
            ].map((s, i) => (
              <StatBadge key={i} {...s} />
            ))}
          </motion.div>
        </div>

        {/* Scroll hint → features */}
        <motion.button
          onClick={() => scrollToSection('features')}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-slate-500 hover:text-slate-300 transition-colors"
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <ChevronDown size={24} />
        </motion.button>
      </section>

      {/* ── FEATURES ────────────────────────────────────────────── */}
      <section id="features" className="relative z-10 py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <RevealSection>
            <div className="text-center mb-16">
              <span className="inline-block px-3 py-1 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-300 text-xs font-medium uppercase tracking-wider mb-4">
                Funcionalidades
              </span>
              <h2 className="text-4xl md:text-5xl font-bold font-heading text-white mb-4">
                Tecnologia que cuida
              </h2>
              <p className="text-slate-400 text-lg max-w-xl mx-auto">
                Cada funcionalidade foi pensada para criar uma experiência terapêutica
                única, segura e eficaz.
              </p>
            </div>
          </RevealSection>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              {
                icon: Brain,
                title: 'IA Terapêutica',
                description:
                  'Baseada na abordagem humanística de Carl Rogers, com respostas empáticas e personalizadas para cada sessão.',
                color: '#4A90E2',
                delay: 0,
              },
              {
                icon: RefreshCw,
                title: 'Continuidade entre Sessões',
                description:
                  'Contexto e progresso mantidos entre sessões, criando uma jornada terapêutica coerente e evolutiva.',
                color: '#6ED2E8',
                delay: 0.1,
              },
              {
                icon: Eye,
                title: 'Análise Emocional',
                description:
                  'Detecção de emoções via webcam em tempo real, integrando dados faciais e textuais para respostas mais precisas.',
                color: '#B28DFF',
                delay: 0.2,
              },
              {
                icon: Mic,
                title: 'Voz Neural',
                description:
                  'Síntese de voz natural em Português Brasileiro via Google Cloud, tornando cada resposta mais humana.',
                color: '#4AD9D9',
                delay: 0.3,
              },
              {
                icon: Shield,
                title: 'Privacidade Total',
                description:
                  'Dados completamente isolados por usuário, com criptografia e validação dupla em todas as operações.',
                color: '#22C55E',
                delay: 0.4,
              },
              {
                icon: Zap,
                title: 'Sessões Automáticas',
                description:
                  'A IA gera automaticamente as próximas sessões com base no seu progresso, mantendo o foco terapêutico.',
                color: '#F59E0B',
                delay: 0.5,
              },
            ].map((f) => (
              <FeatureCard key={f.title} {...f} />
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ────────────────────────────────────────── */}
      <section id="como-funciona" className="relative z-10 py-24 px-6 overflow-hidden">
        <div
          className="absolute inset-0 opacity-30"
          style={{ background: 'radial-gradient(ellipse 80% 50% at 50% 50%, rgba(74,144,226,0.08) 0%, transparent 70%)' }}
        />
        <div className="max-w-6xl mx-auto relative z-10">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <div>
              <RevealSection>
                <span className="inline-block px-3 py-1 rounded-full bg-secondary-500/10 border border-secondary-500/20 text-secondary-300 text-xs font-medium uppercase tracking-wider mb-4">
                  Como funciona
                </span>
                <h2 className="text-4xl md:text-5xl font-bold font-heading text-white mb-4">
                  Sua jornada de
                  <br />
                  <span className="text-secondary-400">bem-estar</span>
                </h2>
                <p className="text-slate-400 text-base leading-relaxed">
                  Do primeiro acesso à evolução contínua — cada passo é pensado para
                  oferecer suporte terapêutico real e progressivo.
                </p>
              </RevealSection>
            </div>

            <div>
              {[
                {
                  number: 1,
                  title: 'Crie seu perfil',
                  description:
                    'Um onboarding estruturado coleta suas informações de forma empática, construindo seu perfil terapêutico personalizado.',
                  delay: 0,
                },
                {
                  number: 2,
                  title: 'Inicie sua primeira sessão',
                  description:
                    'A IA inicia uma conversa contextualizada, adaptando a abordagem ao seu perfil e necessidades.',
                  delay: 0.15,
                },
                {
                  number: 3,
                  title: 'Evolua com continuidade',
                  description:
                    'Cada sessão é memorizada e analisada, gerando automaticamente a próxima sessão com foco no seu crescimento.',
                  delay: 0.3,
                },
                {
                  number: 4,
                  title: 'Acompanhe seu progresso',
                  description:
                    'Visualize sua evolução emocional e terapêutica ao longo do tempo com relatórios e análises detalhadas.',
                  delay: 0.45,
                },
              ].map((s) => (
                <StepCard key={s.number} {...s} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── TECH HIGHLIGHT ──────────────────────────────────────── */}
      <section className="relative z-10 py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <RevealSection>
            <div className="relative rounded-3xl overflow-hidden border border-white/10 p-10 md:p-16"
              style={{ background: 'linear-gradient(135deg, rgba(74,144,226,0.1) 0%, rgba(110,210,232,0.08) 50%, rgba(178,141,255,0.1) 100%)' }}
            >
              <div className="absolute top-0 right-0 w-80 h-80 opacity-20 pointer-events-none"
                style={{ background: 'radial-gradient(circle, rgba(74,217,217,0.5) 0%, transparent 70%)' }}
              />
              <div className="grid md:grid-cols-2 gap-12 items-center relative z-10">
                <div>
                  <h2 className="text-4xl font-bold font-heading text-white mb-4">
                    Arquitetura de
                    <br />
                    <span className="bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
                      microserviços
                    </span>
                  </h2>
                  <p className="text-slate-400 leading-relaxed mb-6">
                    Construída sobre uma arquitetura robusta com serviços independentes
                    para IA, análise emocional, síntese de voz e gestão de sessões —
                    garantindo escalabilidade e resiliência.
                  </p>
                  <motion.button
                    onClick={() => navigate('/login')}
                    className="inline-flex items-center gap-2 text-primary-400 font-semibold hover:text-primary-300 transition-colors"
                    whileHover={{ x: 2 }}
                  >
                    Experimentar agora <ArrowRight size={16} />
                  </motion.button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { name: 'GPT-4o', desc: 'Processamento IA', color: '#4A90E2' },
                    { name: 'OpenFace', desc: 'Emoção facial', color: '#6ED2E8' },
                    { name: 'Google TTS', desc: 'Voz neural', color: '#B28DFF' },
                    { name: 'MongoDB', desc: 'Persistência', color: '#4AD9D9' },
                    { name: 'FastAPI', desc: 'Gateway API', color: '#22C55E' },
                    { name: 'React 18', desc: 'Interface', color: '#F59E0B' },
                  ].map((t, i) => (
                    <motion.div
                      key={t.name}
                      className="p-4 rounded-xl border border-white/10 bg-white/5"
                      initial={{ opacity: 0, scale: 0.8 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.07 }}
                      viewport={{ once: true }}
                      whileHover={{ y: -1, borderColor: `${t.color}50` }}
                    >
                      <div className="text-sm font-bold text-white font-heading">{t.name}</div>
                      <div className="text-xs mt-0.5" style={{ color: t.color }}>{t.desc}</div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────── */}
      <section className="relative z-10 py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <RevealSection>
            <motion.div
              className="relative inline-block mb-6"
              animate={{ rotate: [0, 5, -5, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            >
              <div
                className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto"
                style={{
                  background: 'linear-gradient(135deg, #4A90E2, #6ED2E8)',
                  boxShadow: '0 0 40px rgba(74,144,226,0.4)',
                }}
              >
                <Heart size={36} className="text-white" />
              </div>
            </motion.div>
            <h2 className="text-4xl md:text-5xl font-bold font-heading text-white mb-4">
              Comece sua jornada
              <br />
              <span className="bg-gradient-to-r from-primary-400 via-secondary-400 to-accent-400 bg-clip-text text-transparent">
                hoje mesmo
              </span>
            </h2>
            <p className="text-slate-400 text-lg mb-10 max-w-xl mx-auto">
              Dê o primeiro passo rumo ao bem-estar com suporte terapêutico
              inteligente, disponível sempre que você precisar.
            </p>
            <motion.button
              onClick={() => navigate('/login')}
              className="group inline-flex items-center gap-3 rounded-xl px-8 py-3.5 text-base font-semibold text-white shadow-sm"
              style={{ background: 'linear-gradient(135deg, #4A90E2 0%, #6ED2E8 50%, #B28DFF 100%)' }}
              whileHover={{ y: -1, boxShadow: '0 12px 30px rgba(74,144,226,0.28)' }}
              whileTap={{ y: 0 }}
            >
              Ir para o App
              <motion.span
                animate={{ x: [0, 5, 0] }}
                transition={{ duration: 1.2, repeat: Infinity }}
              >
                <ArrowRight size={22} />
              </motion.span>
            </motion.button>
          </RevealSection>
        </div>
      </section>

      {/* ── CONTACT / AUTHOR ────────────────────────────────────── */}
      <section id="contato" className="relative z-10 py-16 px-6 border-t border-white/10">
        <div className="max-w-6xl mx-auto">
          <RevealSection>
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <h3 className="text-2xl font-bold font-heading text-white mb-2">
                  Fale com o autor
                </h3>
                <p className="text-slate-400 text-sm mb-6">
                  Empat.IA é um projeto criado com propósito: democratizar o acesso ao
                  suporte em saúde mental usando o que há de mais avançado em IA.
                </p>
                <div className="space-y-3">
                  <motion.a
                    href="tel:+5512988334701"
                    className="flex items-center gap-3 text-slate-300 hover:text-white transition-colors group"
                    whileHover={{ x: 4 }}
                  >
                    <div className="w-9 h-9 rounded-lg bg-primary-500/15 border border-primary-500/20 flex items-center justify-center group-hover:bg-primary-500/25 transition-colors">
                      <Phone size={15} className="text-primary-400" />
                    </div>
                    <span className="text-sm font-medium">+55 (12) 98833-4701</span>
                  </motion.a>
                  <motion.a
                    href="mailto:toni.rc.neto@gmail.com"
                    className="flex items-center gap-3 text-slate-300 hover:text-white transition-colors group"
                    whileHover={{ x: 4 }}
                  >
                    <div className="w-9 h-9 rounded-lg bg-secondary-500/15 border border-secondary-500/20 flex items-center justify-center group-hover:bg-secondary-500/25 transition-colors">
                      <Mail size={15} className="text-secondary-400" />
                    </div>
                    <span className="text-sm font-medium">toni.rc.neto@gmail.com</span>
                  </motion.a>
                </div>
              </div>

              <div className="flex justify-center md:justify-end">
                <motion.div
                  className="relative p-8 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm text-center max-w-xs w-full"
                  whileHover={{ y: -4 }}
                >
                  <div
                    className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center text-2xl font-bold font-heading"
                    style={{ background: 'linear-gradient(135deg, #4A90E2, #B28DFF)' }}
                  >
                    T
                  </div>
                  <div className="text-white font-semibold font-heading text-lg">Toni R. C. Neto</div>
                  <div className="text-primary-400 text-sm mt-1">Fundador & Desenvolvedor</div>
                  <p className="text-slate-500 text-xs mt-3 leading-relaxed">
                    Apaixonado por tecnologia e bem-estar humano, criando soluções que
                    unem IA e psicologia para impacto real.
                  </p>
                </motion.div>
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ── FOOTER ──────────────────────────────────────────────── */}
      <footer className="py-8 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #4A90E2, #6ED2E8)' }}
            >
              <Brain size={14} className="text-white" />
            </div>
            <span className="text-sm font-bold font-heading text-white">
              Empat<span className="text-primary-400">.IA</span>
            </span>
          </div>
          <p className="text-xs text-slate-600 text-center">
            © {new Date().getFullYear()} Empat.IA · Terapia Virtual Inteligente · Todos os direitos reservados
          </p>
          <motion.button
            onClick={() => navigate('/login')}
            className="text-xs text-primary-400 font-medium hover:text-primary-300 flex items-center gap-1 transition-colors"
            whileHover={{ x: 1 }}
          >
            Acessar o App <ArrowRight size={12} />
          </motion.button>
        </div>
      </footer>
    </div>
  );
}
