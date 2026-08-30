import { Injectable, signal } from '@angular/core';

export type ToastType = 'success' | 'error' | 'info';

export interface ToastMessage {
  id: number;
  type: ToastType;
  title: string;
  message: string;
  closing?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private nextId = 1;
  public toasts = signal<ToastMessage[]>([]);

  show(type: ToastType, title: string, message: string, durationMs = 3000) {
    const id = this.nextId++;
    const newToast: ToastMessage = { id, type, title, message };
    
    this.toasts.update(toasts => [...toasts, newToast]);

    if (durationMs > 0) {
      setTimeout(() => {
        this.remove(id);
      }, durationMs);
    }
  }

  success(title: string, message: string) {
    this.show('success', title, message);
  }

  error(title: string, message: string) {
    this.show('error', title, message);
  }

  info(title: string, message: string) {
    this.show('info', title, message);
  }

  remove(id: number) {
    // 標記為正在關閉，以觸發退出動畫
    this.toasts.update(toasts => 
      toasts.map(t => t.id === id ? { ...t, closing: true } : t)
    );

    // 等待動畫結束後從陣列中移除 (動畫設定為 0.3s)
    setTimeout(() => {
      this.toasts.update(toasts => toasts.filter(t => t.id !== id));
    }, 300);
  }
}
