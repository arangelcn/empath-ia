import { useState, useEffect } from 'react';
import Lottie from 'lottie-react';

export default function AvatarDog() {
  const [animationData, setAnimationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnimation = async () => {
      try {
        const response = await fetch('/dog-animation.json');
        if (!response.ok) {
          throw new Error('Failed to load animation');
        }
        const data = await response.json();
        setAnimationData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAnimation();
  }, []);

  if (loading) {
    return (
      <div style={{ width: 200, margin: "0 auto", textAlign: "center" }}>
        <div className="animate-pulse">
          <div className="w-48 h-48 bg-gray-200 rounded-lg"></div>
          <p className="text-sm text-gray-500 mt-2">Carregando animação...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ width: 200, margin: "0 auto", textAlign: "center" }}>
        <div className="text-red-500">
          <p className="text-sm">Erro ao carregar animação</p>
          <p className="text-xs text-gray-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ width: 200, margin: "0 auto" }}>
      <Lottie 
        animationData={animationData} 
        loop={true}
        autoplay={true}
        style={{ width: "100%", height: "auto" }}
      />
    </div>
  );
} 