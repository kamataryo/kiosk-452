declare module 'socket.io-client' {
  export interface Socket {
    id: string;
    connected: boolean;
    disconnected: boolean;

    on(event: string, listener: (...args: any[]) => void): Socket;
    emit(event: string, ...args: any[]): Socket;
    off(event?: string, listener?: (...args: any[]) => void): Socket;
    close(): Socket;
  }

  export interface ManagerOptions {
    forceNew?: boolean;
    multiplex?: boolean;
    timeout?: number;
    transports?: string[];
    upgrade?: boolean;
    rememberUpgrade?: boolean;
    path?: string;
    query?: object;
    extraHeaders?: object;
  }

  export function io(uri?: string, options?: ManagerOptions): Socket;
}
