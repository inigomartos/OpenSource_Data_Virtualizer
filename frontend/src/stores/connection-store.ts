import { create } from 'zustand';
import type { Connection } from '@/types/connection';

interface ConnectionState {
  connections: Connection[];
  activeConnectionId: string | null;

  setConnections: (connections: Connection[]) => void;
  setActiveConnection: (id: string | null) => void;
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  connections: [],
  activeConnectionId: null,

  setConnections: (connections) => set({ connections }),
  setActiveConnection: (id) => set({ activeConnectionId: id }),
}));
