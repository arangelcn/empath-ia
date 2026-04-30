import React, { useEffect, useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { CheckCircle2, Loader2, Mail, Save, User, Volume2 } from 'lucide-react';
import { getUser, updateUserPreferences } from '../../services/api.js';

const voiceOptions = [
  {
    id: 'pt-BR-Neural2-B',
    label: 'Voz Masculina Confiante',
    description: 'Tom seguro e profissional',
  },
  {
    id: 'pt-BR-Neural2-A',
    label: 'Voz Feminina Suave',
    description: 'Tom suave e acolhedor',
  },
  {
    id: 'pt-BR-Wavenet-A',
    label: 'Voz Feminina Profissional',
    description: 'Tom claro e objetivo',
  },
  {
    id: 'pt-BR-Wavenet-B',
    label: 'Voz Masculina Amigavel',
    description: 'Tom caloroso e proximo',
  },
  {
    id: 'pt-BR-Wavenet-C',
    label: 'Voz Feminina Calorosa',
    description: 'Tom empatico e compreensivo',
  },
];

const readLocalUser = () => {
  const candidates = ['empatia_user_data', 'empatia_user'];

  for (const key of candidates) {
    const raw = localStorage.getItem(key);
    if (!raw) continue;

    try {
      return JSON.parse(raw);
    } catch {
      // Ignore corrupted local data.
    }
  }

  return null;
};

const ProfileVoicePage = () => {
  const { username, selectedVoice, setSelectedVoice } = useOutletContext();
  const [user, setUser] = useState(null);
  const [displayName, setDisplayName] = useState('');
  const [voice, setVoice] = useState(selectedVoice || 'pt-BR-Neural2-B');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const localUser = useMemo(readLocalUser, []);
  const preferences = user?.preferences || {};
  const email = user?.email || localUser?.email || username;

  useEffect(() => {
    const loadUser = async () => {
      if (!username) {
        setError('Usuario nao encontrado.');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError('');
        const response = await getUser(username);
        const userData = response.data || {};
        const nextPreferences = userData.preferences || {};

        setUser(userData);
        setDisplayName(
          nextPreferences.display_name
          || nextPreferences.full_name
          || localUser?.name
          || userData.email
          || username
        );
        setVoice(nextPreferences.selected_voice || selectedVoice || localStorage.getItem('empatia_selected_voice') || 'pt-BR-Neural2-B');
      } catch (err) {
        console.error('Erro ao carregar perfil:', err);
        setUser({
          username,
          email: localUser?.email,
          preferences: {
            selected_voice: selectedVoice || localStorage.getItem('empatia_selected_voice') || 'pt-BR-Neural2-B',
            voice_enabled: true,
          },
        });
        setDisplayName(localUser?.name || username);
        setVoice(selectedVoice || localStorage.getItem('empatia_selected_voice') || 'pt-BR-Neural2-B');
        setError('Nao foi possivel carregar todos os dados salvos.');
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, [localUser, selectedVoice, username]);

  useEffect(() => {
    if (!success) return undefined;

    const timer = window.setTimeout(() => setSuccess(''), 5000);
    return () => window.clearTimeout(timer);
  }, [success]);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!username) {
      setError('Usuario nao encontrado.');
      return;
    }

    try {
      setSaving(true);
      setError('');
      setSuccess('');

      const nextPreferences = {
        ...preferences,
        display_name: displayName.trim(),
        selected_voice: voice,
        voice_enabled: preferences.voice_enabled ?? true,
        theme: preferences.theme || 'dark',
        language: preferences.language || 'pt-BR',
      };

      await updateUserPreferences(username, nextPreferences);
      setUser(prev => ({
        ...(prev || {}),
        username,
        email,
        preferences: nextPreferences,
      }));

      localStorage.setItem('empatia_selected_voice', voice);
      setSelectedVoice?.(voice);

      const storedUser = readLocalUser();
      if (storedUser) {
        const nextUser = {
          ...storedUser,
          name: displayName.trim() || storedUser.name,
          display_name: displayName.trim(),
        };
        if (localStorage.getItem('empatia_user_data')) {
          localStorage.setItem('empatia_user_data', JSON.stringify(nextUser));
        }
        if (localStorage.getItem('empatia_user')) {
          localStorage.setItem('empatia_user', JSON.stringify(nextUser));
        }
      }

      setSuccess('Perfil e voz atualizados.');
    } catch (err) {
      console.error('Erro ao salvar perfil:', err);
      setError('Nao foi possivel salvar agora. Tente novamente.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background-light px-4">
        <div className="flex items-center gap-3 text-sm font-medium text-gray-600">
          <Loader2 className="h-5 w-5 animate-spin text-primary-600" />
          Carregando perfil...
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background-light px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-6">
          <p className="mb-2 text-xs font-semibold uppercase text-primary-600">Conta</p>
          <h1 className="font-heading text-3xl font-bold text-gray-950">Perfil e voz</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-gray-600">
            Ajuste como voce aparece no Empat.IA e escolha a voz usada nas conversas.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
              {error}
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
              <CheckCircle2 className="h-4 w-4" />
              {success}
            </div>
          )}

          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
                <User className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-950">Dados do usuario</h2>
                <p className="text-sm text-gray-500">Informacoes basicas da sua conta.</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-gray-700">Nome exibido</span>
                <input
                  type="text"
                  value={displayName}
                  onChange={event => setDisplayName(event.target.value)}
                  className="w-full rounded-lg border-gray-200 bg-white text-sm text-gray-900 focus:border-primary-500 focus:ring-primary-500"
                  placeholder="Como devemos te chamar?"
                />
              </label>

              <div>
                <span className="mb-2 block text-sm font-medium text-gray-700">Email / usuario tecnico</span>
                <div className="flex min-h-[44px] items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm text-gray-600">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <span className="min-w-0 truncate">{email}</span>
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
                <Volume2 className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-950">Voz da IA</h2>
                <p className="text-sm text-gray-500">Essa voz sera usada nas proximas respostas com audio.</p>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              {voiceOptions.map(option => {
                const isSelected = voice === option.id;

                return (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => setVoice(option.id)}
                    className={[
                      'flex min-h-[78px] items-start gap-3 rounded-lg border p-4 text-left transition-colors',
                      isSelected
                        ? 'border-primary-500 bg-primary-50 text-primary-900'
                        : 'border-gray-200 bg-white text-gray-700 hover:border-primary-200 hover:bg-gray-50',
                    ].join(' ')}
                  >
                    <span className={[
                      'mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border',
                      isSelected ? 'border-primary-600 bg-primary-600 text-white' : 'border-gray-300 bg-white',
                    ].join(' ')}>
                      {isSelected && <CheckCircle2 className="h-3.5 w-3.5" />}
                    </span>
                    <span>
                      <span className="block text-sm font-semibold">{option.label}</span>
                      <span className="mt-1 block text-sm text-gray-500">{option.description}</span>
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-lg bg-primary-600 px-5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Salvando...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Salvar alteracoes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
};

export default ProfileVoicePage;
