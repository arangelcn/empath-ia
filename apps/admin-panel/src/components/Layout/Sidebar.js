import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { 
  XMarkIcon,
  HomeIcon,
  FaceSmileIcon,
  SpeakerWaveIcon,
  CpuChipIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Configurações de Emoção', href: '/emotion-settings', icon: FaceSmileIcon },
  { name: 'Configurações de Áudio', href: '/audio-settings', icon: SpeakerWaveIcon },
  { name: 'Status do Sistema', href: '/system-status', icon: CpuChipIcon },
  { name: 'Monitor em Tempo Real', href: '/monitor', icon: ChartBarIcon },
  { name: 'Configurações Gerais', href: '/settings', icon: Cog6ToothIcon },
];

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

export default function Sidebar({ open, setOpen }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const SidebarContent = () => (
    <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4 border-r border-gray-200">
      <div className="flex h-16 shrink-0 items-center">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <FaceSmileIcon className="w-5 h-5 text-white" />
          </div>
          <span className="ml-3 text-xl font-semibold text-gray-900">Empath IA</span>
        </div>
      </div>
      <nav className="flex flex-1 flex-col">
        <ul role="list" className="flex flex-1 flex-col gap-y-7">
          <li>
            <ul role="list" className="-mx-2 space-y-1">
              {navigation.map((item) => (
                <li key={item.name}>
                  <button
                    onClick={() => navigate(item.href)}
                    className={classNames(
                      location.pathname === item.href
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50',
                      'group flex w-full gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold transition-colors duration-200'
                    )}
                  >
                    <item.icon
                      className={classNames(
                        location.pathname === item.href ? 'text-primary-600' : 'text-gray-400 group-hover:text-primary-600',
                        'h-6 w-6 shrink-0'
                      )}
                      aria-hidden="true"
                    />
                    {item.name}
                  </button>
                </li>
              ))}
            </ul>
          </li>
          <li className="mt-auto">
            <div className="flex items-center gap-x-4 px-2 py-3 text-sm font-semibold leading-6 text-gray-900 border-t border-gray-200">
              <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {user?.name?.charAt(0) || 'A'}
                </span>
              </div>
              <div className="flex-1">
                <span className="sr-only">Sua conta</span>
                <span aria-hidden="true">{user?.name || 'Admin'}</span>
              </div>
              <button
                onClick={handleLogout}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                title="Sair"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
              </button>
            </div>
          </li>
        </ul>
      </nav>
    </div>
  );

  return (
    <>
      {/* Mobile sidebar */}
      <Transition.Root show={open} as={Fragment}>
        <Dialog as="div" className="relative z-50 lg:hidden" onClose={setOpen}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-gray-900/80" />
          </Transition.Child>

          <div className="fixed inset-0 flex">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                <Transition.Child
                  as={Fragment}
                  enter="ease-in-out duration-300"
                  enterFrom="opacity-0"
                  enterTo="opacity-100"
                  leave="ease-in-out duration-300"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                    <button type="button" className="-m-2.5 p-2.5" onClick={() => setOpen(false)}>
                      <span className="sr-only">Fechar sidebar</span>
                      <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
                    </button>
                  </div>
                </Transition.Child>
                <SidebarContent />
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>

      {/* Static sidebar for desktop */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
        <SidebarContent />
      </div>
    </>
  );
} 