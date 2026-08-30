import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastService } from '../../services/toast';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './toast.html',
  styleUrl: './toast.css',
})
export class Toast {
  toastService = inject(ToastService);

  getIconClass(type: string): string {
    const icons: Record<string, string> = {
      success: 'fa-solid fa-circle-check text-green-500 text-xl',
      error: 'fa-solid fa-circle-exclamation text-red-500 text-xl',
      info: 'fa-solid fa-circle-info text-blue-500 text-xl'
    };
    return icons[type] || icons['info'];
  }

  getBorderColor(type: string): string {
    const borders: Record<string, string> = {
      success: 'border-green-500',
      error: 'border-red-500',
      info: 'border-blue-500'
    };
    return borders[type] || borders['info'];
  }
}
